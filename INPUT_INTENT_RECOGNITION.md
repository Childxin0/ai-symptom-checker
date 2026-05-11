# 输入意图识别功能文档

## 功能概述

本系统新增**输入意图识别层**，在进入症状结构化和风险分层前，先判断用户输入是否属于有效的医疗症状描述。这可以防止系统将非医疗内容（如项目规划、编程问题等）误判为低风险症状，并为信息不足的输入提供追问引导。

---

## 三种输入状态

### 1. `valid_symptom` - 有效症状输入
**定义**：包含明确症状描述和足够细节的医疗输入

**识别条件**：
- 包含紧急症状关键词（如：车祸、大出血、呼吸困难、昏迷等）
- **或** 包含症状关键词 + 有具体细节（持续时间、严重程度、部位等）

**系统行为**：
- 进入完整分析流程（症状结构化 + 风险评估）
- 显示风险等级、分数、建议、推荐科室

**示例**：
- "头疼三天，发烧38.5度，恶心"
- "被车撞了，大出血"
- "胸口剧烈疼痛，喘不上气"
- "右下腹持续疼痛8小时"

---

### 2. `insufficient_symptom` - 信息不足
**定义**：可能是症状描述，但缺少足够的细节信息

**识别条件**：
- 包含健康关注表达（"不舒服"、"难受"、"不适"等）
- **但** 文本过短（< 10字）或缺少具体症状词和细节

**系统行为**：
- **不进行** 症状结构化和风险评估
- 显示"需要更多信息"提示
- 生成4个标准追问问题：
  1. 具体不适部位
  2. 持续时间
  3. 严重程度
  4. 伴随症状

**示例**：
- "我不舒服"
- "感觉不太好"
- "身体有点怪"
- "难受"

---

### 3. `non_medical_input` - 非医疗输入
**定义**：明确不属于医疗症状描述的内容

**识别条件**：
- 包含非医疗关键词（如：项目、代码、简历、部署、编程等）
- **或** 匹配典型非医疗模式（"如何部署"、"帮我写"等）

**系统行为**：
- **不进行** 症状结构化和风险评估
- 显示"输入不符合症状描述"提示
- 引导用户输入有效的医疗症状描述
- **不显示** 风险等级、分数、推荐科室

**示例**：
- "更好的升级方向：做成AI医疗PM面试杀器版"
- "帮我写简历"
- "这个项目怎么部署到Vercel"
- "如何配置React项目"

---

## 技术实现

### 后端模块

#### 1. `backend/core/input_validator.py`
**核心验证模块**

**关键函数**：
```python
def validate_input(user_input: str) -> Tuple[InputType, str]:
    """
    识别输入意图
    Returns: (input_type, validation_message)
    """
```

**验证逻辑**：
1. 检查是否为非医疗内容（强排除）
2. 检查是否包含紧急症状关键词
3. 检查是否包含症状关键词 + 细节
4. 判断信息充分度

**关键词库**：
- `SYMPTOM_KEYWORDS`: 症状词（疼、痛、发烧、咳嗽、出血等）
- `EMERGENCY_KEYWORDS`: 紧急症状（车祸、大出血、昏迷、自杀等）
- `HEALTH_CONCERN_PHRASES`: 健康关注（不舒服、难受、身体等）
- `NON_MEDICAL_KEYWORDS`: 非医疗词（代码、项目、简历、部署等）

---

#### 2. `backend/core/models.py`
**更新后的响应模型**

```python
class AnalysisResult(BaseModel):
    input_type: Literal["valid_symptom", "insufficient_symptom", "non_medical_input"]
    input_validation_message: str
    structured: Optional[StructuredSymptoms]  # 仅valid_symptom时有值
    risk: Optional[RiskAssessment]  # 仅valid_symptom时有值
    # ... 其他字段
```

---

#### 3. `backend/api/routes.py`
**集成到API流程**

```python
@router.post("/analyze")
async def analyze_symptoms(request: AnalyzeRequest):
    # 1. 输入意图识别（新增）
    input_type, validation_message = validate_input(user_input)
    
    if input_type == "non_medical_input":
        # 直接返回提示，不进行分析
        return AnalysisResult(
            input_type=input_type,
            input_validation_message=validation_message,
            structured=None,
            risk=None,
            ...
        )
    
    elif input_type == "insufficient_symptom":
        # 返回追问问题
        return AnalysisResult(
            input_type=input_type,
            needs_followup=True,
            followup_questions=[...],
            ...
        )
    
    # 2. 有效症状：进入完整分析流程
    ...
```

---

### 前端组件

#### `frontend/src/components/ResultPanel.jsx`
**条件渲染逻辑**

```jsx
export default function ResultPanel({ result }) {
  // 非医疗输入：显示警告和引导
  if (result.input_type === 'non_medical_input') {
    return <AmberWarningCard />
  }
  
  // 信息不足：显示追问问题
  if (result.input_type === 'insufficient_symptom') {
    return <BlueFollowupCard />
  }
  
  // 有效症状：显示完整分析结果
  return <FullAnalysisPanel />
}
```

**UI设计**：
- `non_medical_input`: 琥珀色警告卡，提供输入示例
- `insufficient_symptom`: 蓝色信息卡，列出4个追问问题
- `valid_symptom`: 完整分析面板（症状识别、风险卡片、建议、科室）

---

## 测试验证

### 测试脚本
`backend/test_input_recognition.py`

### 测试结果
**9/9 全部通过** ✓

| 输入文本 | 预期类型 | 实际结果 | 状态 |
|---------|---------|---------|------|
| 更好的升级方向：做成AI医疗PM面试杀器版 | non_medical_input | ✓ | PASS |
| 帮我写简历 | non_medical_input | ✓ | PASS |
| 这个项目怎么部署到Vercel | non_medical_input | ✓ | PASS |
| 我感觉不太舒服 | insufficient_symptom | ✓ | PASS |
| 不舒服 | insufficient_symptom | ✓ | PASS |
| 身体有点怪 | insufficient_symptom | ✓ | PASS |
| 头疼三天，发烧38.5度，恶心 | valid_symptom → MEDIUM | ✓ | PASS |
| 被车撞了，大出血 | valid_symptom → EMERGENCY | ✓ | PASS |
| 胸口剧烈疼痛，喘不上气 | valid_symptom → EMERGENCY | ✓ | PASS |

---

## 产品价值

### 1. 防止误判
- 非医疗输入不再被识别为"低风险"
- 避免系统对无关内容给出医疗建议

### 2. 提升用户体验
- 清晰的错误提示和输入引导
- 针对性的追问，帮助用户补充信息

### 3. 提高准确性
- 只对有效症状进行风险评估
- 减少低质量输入导致的误判

### 4. 系统安全性
- 明确区分医疗和非医疗场景
- 避免对非症状输入进行不当的医疗建议

---

## 使用方式

### 前端测试
1. 启动后端：`cd backend && uvicorn main:app --reload`
2. 启动前端：`cd frontend && npm run dev`
3. 访问：`http://localhost:5173`

### 测试用例
**非医疗输入**：
- "帮我写简历"
- "如何部署项目"

**信息不足**：
- "不舒服"
- "感觉不太好"

**有效症状**：
- "头疼三天，发烧38度"
- "被车撞了，大出血"

---

## 后续优化方向

1. **扩展关键词库**：
   - 增加更多医疗和非医疗关键词
   - 支持更多口语化表达

2. **引入LLM增强**：
   - 对模糊边界情况使用LLM判断
   - 提升识别准确性

3. **多轮对话优化**：
   - 对`insufficient_symptom`生成个性化追问
   - 记录多轮补充信息

4. **国际化支持**：
   - 支持多语言输入识别
   - 扩展非中文关键词库

---

## 总结

输入意图识别层的引入，显著提升了系统的**鲁棒性**和**用户体验**。通过三种状态的精确分类，系统能够：
- ✓ 过滤非医疗输入
- ✓ 引导信息不足的用户
- ✓ 对有效症状进行准确风险评估

这是一个**产品级的设计改进**，为后续功能扩展奠定了坚实基础。
