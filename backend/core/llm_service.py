"""
LLM 服务 - OpenAI-compatible API 调用
兼容 DeepSeek / SiliconFlow / OpenAI 等所有 OpenAI-compatible 后端
两阶段 Pipeline：症状结构化 → 风险解释生成
"""
import json
import re
from typing import Optional, Tuple
from openai import OpenAI, APIConnectionError, AuthenticationError, BadRequestError

from core.config import get_settings
from core.models import StructuredSymptoms, RiskAssessment, FollowupQuestion


def _build_client() -> Optional[OpenAI]:
    """构建 OpenAI-compatible 客户端，并在日志中明确显示配置状态"""
    settings = get_settings()

    if not settings.llm_api_key:
        print("[LLM] ERROR: LLM_API_KEY 未配置，LLM 功能不可用")
        return None

    print(f"[LLM] 初始化客户端 base_url={settings.llm_base_url} model={settings.llm_model}")
    return OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=settings.llm_timeout,
    )


def _call_llm(client: OpenAI, messages: list, max_tokens: int = 1024, temperature: float = 0.2) -> str:
    """
    统一 LLM 调用入口，明确区分并日志输出各类错误。
    Returns: 模型回复文本
    Raises: Exception（已在日志中记录具体原因）
    """
    settings = get_settings()
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
    except AuthenticationError as e:
        print(f"[LLM] LLM call failed: API Key 无效或已过期 → {e}")
        raise
    except APIConnectionError as e:
        print(f"[LLM] LLM call failed: 无法连接到 {settings.llm_base_url}，请检查 LLM_BASE_URL → {e}")
        raise
    except BadRequestError as e:
        print(f"[LLM] LLM call failed: 请求参数错误，请检查 LLM_MODEL={settings.llm_model} 是否正确 → {e}")
        raise
    except Exception as e:
        print(f"[LLM] LLM call failed: {type(e).__name__}: {e}")
        raise


class LLMService:
    """LLM 调用服务（OpenAI-compatible）"""

    def __init__(self):
        self.settings = get_settings()
        self.client = _build_client()

    async def structure_symptoms(self, user_input: str) -> Tuple[Optional[StructuredSymptoms], Optional[str]]:
        """
        第一阶段：症状结构化

        Returns:
            (StructuredSymptoms | None, error_message | None)
        """
        if not self.client:
            return None, "LLM_API_KEY 未配置，无法调用 LLM"

        system_msg = "你是医疗初筛系统的症状分析助手。严格按照用户要求输出JSON，不添加任何额外文字或markdown。"
        user_msg = f"""请将以下症状描述转换为结构化JSON。

用户描述：
{user_input}

请输出严格的JSON格式（不要markdown代码块）：
{{
  "symptoms": ["列出识别到的所有症状"],
  "duration": "持续时间描述",
  "severity": "轻度/中度/重度/未知",
  "body_location": "身体部位",
  "accompanying_symptoms": ["伴随症状列表"],
  "medical_history_mentioned": true/false,
  "symptom_onset": "突发/渐进/不确定",
  "temperature": 体温数值（如有）或null,
  "additional_context": "其他重要信息"
}}

关键要求：
1. **幻觉约束（最高优先级，铁律）**：
   - symptoms 和 accompanying_symptoms 字段**只能包含用户明确说出的症状**
   - **严禁**推断、联想、扩展或补充用户未提及的症状
   - 如果用户只说了一个症状，symptoms 列表**只能有一个条目**
   - 如果用户描述模糊（如"感觉不对"、"很难受"），symptoms 应为空列表 []
   - 示例：
     - 用户说"头疼" → symptoms: ["头痛"]，**绝不**添加"恶心"、"发烧"、"呕吐"
     - 用户说"咳嗽" → symptoms: ["咳嗽"]，**绝不**添加"流鼻涕"、"发烧"
     - 用户说"浑身不舒服" → symptoms: []（描述太模糊，不推断具体症状）

2. **否定句处理（同级铁律）**：
   - 如果用户用"没有"、"不是"、"无"、"没"等否定词修饰某症状，该症状**绝对不能**出现在 symptoms 或 accompanying_symptoms 列表中
   - 示例：
     - "我没有发烧，但头很疼" → symptoms 只含"头痛"，不含"发烧"
     - "没有胸痛，但呼吸困难" → symptoms 只含"呼吸困难"，不含"胸痛"
     - "不是头疼，是脖子疼" → symptoms 只含"脖子疼"，不含"头疼"
   - 只列出用户**确认存在**的症状，否定掉的症状一律排除

3. **症状完整性**：symptoms 必须包含所有**肯定描述**的症状

4. **时间提取**：duration 必须从文本中准确提取时间信息
   - 如果没有明确时间，写"未明确说明"，不要写"未知"

5. **体温数值**：从文本中提取体温（如"38.5度"→38.5）

6. **严重程度判断**：根据用户的描述词判断（轻微→轻度，严重/剧烈→重度）

7. 只输出JSON，不要额外解释或markdown代码块标记"""

        try:
            response_text = _call_llm(
                self.client,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=1024,
                temperature=0.1,
            )

            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                return StructuredSymptoms(**data), None
            else:
                print(f"[LLM] LLM call failed: 症状结构化返回格式错误，原始输出: {response_text[:200]}")
                return None, "LLM返回格式错误"

        except Exception as e:
            return None, f"LLM调用失败: {str(e)}"

    async def generate_analysis(
        self,
        user_input: str,
        structured: StructuredSymptoms,
        risk: RiskAssessment
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        第二阶段：生成风险解释和建议

        Returns:
            (analysis_dict | None, error_message | None)
        """
        if not self.client:
            return None, "LLM_API_KEY 未配置，无法调用 LLM"

        symptoms_text = "、".join(structured.symptoms) if structured.symptoms else "无明显症状"
        rules_text = "\n".join(risk.rule_explanations) if risk.rule_explanations else "无"

        system_msg = "你是医疗初筛AI。根据提供的信息生成专业分析报告，只输出JSON，不添加任何额外文字或markdown。"
        user_msg = f"""基于以下信息生成专业的分析报告。

【用户原始描述】
{user_input}

【结构化症状】
症状列表：{symptoms_text}
持续时间：{structured.duration}
严重程度：{structured.severity}
体温：{structured.temperature}°C（如有）
发病方式：{structured.symptom_onset}

【规则引擎判定】
风险等级：{risk.level}
触发规则：
{rules_text}

请生成JSON格式的分析报告（不要markdown代码块）：
{{
  "advice": "详细的就诊建议（自然语言，150-300字）",
  "rationale": "AI推理过程（说明为什么得出该结论，100-200字）",
  "explainability": "面向普通用户的解释（通俗易懂，150-250字）",
  "recommended_department": "推荐科室（如'心内科'、'急诊科'）",
  "urgency_timeline": "紧急程度（如'立即就医'、'24小时内'、'3天内'、'可观察'）"
}}

重要要求：
1. advice 必须根据风险等级给出明确建议：
   - HIGH: 必须包含"立即就医"或"拨打120"
   - MEDIUM: 建议"尽快就医"或"24-48小时内就诊"
   - LOW: 可建议"观察"但需告知何时应就医

2. explainability 要点名触发的规则，用通俗语言解释

3. 所有内容用中文，语气专业但易懂

4. 只输出JSON，不要额外文字"""

        try:
            response_text = _call_llm(
                self.client,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=2048,
                temperature=0.3,
            )

            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                return data, None
            else:
                print(f"[LLM] LLM call failed: 分析生成返回格式错误，原始输出: {response_text[:200]}")
                return None, "LLM返回格式错误"

        except Exception as e:
            return None, f"LLM调用失败: {str(e)}"

    async def classify_intent(self, user_input: str) -> tuple[str, float, str]:
        """
        LLM 意图分类：判断输入是 valid_symptom / insufficient_symptom / non_medical_input

        Returns:
            (input_type, confidence, reason)
        Raises:
            Exception if LLM is unavailable or call fails
        """
        if not self.client:
            raise ValueError("LLM 不可用：LLM_API_KEY 未配置")

        system_msg = "你是医疗分诊助手，只判断用户输入的意图类型，不做诊断。返回严格JSON，不要任何多余文字。"
        user_msg = f"""判断以下输入属于哪种类型：
"{user_input}"

返回严格JSON，不要任何多余文字：
{{
  "input_type": "valid_symptom 或 insufficient_symptom 或 non_medical_input",
  "confidence": 0到1之间的数字,
  "reason": "一句话说明原因"
}}

判断规则：
- valid_symptom：包含具体身体症状，且有足够信息（部位/持续时间/严重程度 至少其一）
- insufficient_symptom：涉及健康/身体/精神状态，但信息不足，需要追问
  覆盖：所有身体不适（含儿童老人场景）、生殖健康、精神心理、慢病状态
  即使只有一个词（"头疼"/"白带异常"/"痛经"），只要健康相关就归这类
  "不想活了"属于心理健康危机 → insufficient_symptom
- non_medical_input：与个人健康完全无关（写代码/写简历/部署项目/学习计划等）
  注意：混合输入中如有身体症状，优先判健康类，不判 non_medical_input"""

        response_text = _call_llm(
            self.client,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=200,
            temperature=0.0,
        )

        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if not json_match:
            raise ValueError(f"LLM 返回格式错误: {response_text[:100]}")

        data = json.loads(json_match.group())
        input_type = data.get("input_type", "insufficient_symptom")
        if input_type not in ("valid_symptom", "insufficient_symptom", "non_medical_input"):
            input_type = "insufficient_symptom"
        confidence = float(data.get("confidence", 0.8))
        reason = str(data.get("reason", ""))
        return input_type, confidence, reason

    @staticmethod
    def _infer_question_type(question: str) -> str:
        """从问题文本推断 question_type"""
        q = question.lower()
        if any(w in q for w in ["多久", "多长时间", "几天", "几小时", "持续", "开始多久", "何时开始"]):
            return "duration"
        if any(w in q for w in ["严重", "程度如何", "轻重", "疼痛程度", "评分"]):
            return "severity"
        if any(w in q for w in ["哪里", "哪个部位", "什么位置", "位置", "部位"]):
            return "location"
        if any(w in q for w in ["是否", "有没有", "有无", "吗？", "吗,"]):
            return "yn"
        if any(w in q for w in ["请描述", "请说明", "请说说", "具体说", "详细"]):
            return "open"
        return "yn"

    async def generate_followup_questions(
        self,
        user_input: str,
        structured: StructuredSymptoms,
        risk: RiskAssessment
    ) -> list[FollowupQuestion]:
        """生成追问问题（含 question_type）"""
        if not self.client or risk.level == "HIGH":
            return []

        system_msg = "你是医疗初筛AI，根据症状信息生成追问问题。只输出JSON数组，不添加任何额外文字或markdown。"
        user_msg = f"""基于当前信息，生成1-2个关键追问问题。

【用户描述】
{user_input}

【已知症状】
{", ".join(structured.symptoms) if structured.symptoms else "无"}

【当前风险】
{risk.level}

请生成JSON格式的追问问题（不要markdown）：
[
  {{
    "question": "追问问题文本（自然语言，面向患者，简洁明了）",
    "category": "time/severity/location/accompanying",
    "question_type": "yn 或 duration 或 severity 或 location 或 open",
    "options": null
  }}
]

question_type 规则（严格遵守）：
- 询问持续时间、多久 → "duration"
- 询问严重程度 → "severity"
- 询问具体部位/位置 → "location"
- 是否类问题（有没有/是否）→ "yn"
- 需要自由描述 → "open"

要求：
1. 最多2个问题，优先选最影响风险判断的维度
2. category 必须是 time/severity/location/accompanying 之一
3. options 字段请填 null
4. 只输出JSON数组，不要额外文字"""

        try:
            response_text = _call_llm(
                self.client,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=512,
                temperature=0.3,
            )

            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                data = json.loads(json_match.group())
                questions = []
                for q in data[:2]:
                    if "question_type" not in q or q["question_type"] not in (
                        "yn", "duration", "severity", "location", "open"
                    ):
                        q["question_type"] = self._infer_question_type(q.get("question", ""))
                    q["options"] = None
                    questions.append(FollowupQuestion(**q))
                return questions
            else:
                print(f"[LLM] 追问生成返回格式错误，原始输出: {response_text[:200]}")
                return []

        except Exception as e:
            print(f"[LLM] LLM call failed: 追问生成失败 → {e}")
            return []


# 单例
_llm_service = None


def get_llm_service() -> LLMService:
    """获取LLM服务单例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


# 完成
