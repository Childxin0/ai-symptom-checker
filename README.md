# AI 症状结构化 + 风险分层系统

*AI Symptom Structuring and Risk Stratification Demo for Portfolio*

![Demo](https://img.shields.io/badge/Demo-Live-22c55e)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-3b82f6)
![Backend](https://img.shields.io/badge/Backend-FastAPI-10b981)
![LLM](https://img.shields.io/badge/LLM-DeepSeek-f59e0b)
![License](https://img.shields.io/badge/License-MIT-64748b)

**在线演示：** [ai-symptom-checker-tau.vercel.app](https://ai-symptom-checker-tau.vercel.app)

> 作品集项目 · AI 医疗 PM 方向 · MVP 级可交互演示

---

## 项目定位

本项目是面向患者自然语言症状输入的 AI 辅助初筛 Demo，用于展示医疗场景下的 AI 产品设计与工程落地能力。  
系统提供风险分层、追问补全、就医建议与可解释性说明，但不构成医疗诊断。

在产品思路上，参考 ADA Health、Buoy Health 等医疗初筛产品的设计路径，重点展示：

- **产品化链路设计**：从自然语言输入到结构化输出与建议反馈
- **风险治理能力**：规则优先、模型辅助的分层机制
- **AI 可解释性**：通过 Explainability 提升用户理解与信任
- **稳定性设计**：在模型异常或输入不完整时提供保守且连续的服务体验

---

## 在线地址

- 在线 Demo：`https://ai-symptom-checker-tau.vercel.app`
- 后端 API：`<待补充>`
- GitHub：`<待补充>`
- 30 秒演示脚本：[`DEMO_SCRIPT.md`](./DEMO_SCRIPT.md)

---

## 核心功能

### 1) 自然语言症状输入
支持口语化中文描述，用户可直接输入完整主诉，如“头疼三天，昨晚发烧 38.5 度”。

### 2) 症状结构化识别
提取症状、持续时间、严重程度、伴随症状、发病方式等字段，为后续风险判断提供结构化输入。

### 3) 风险分层（LOW / MEDIUM / HIGH / EMERGENCY）
系统输出四级风险，并给出对应处理建议：

- `EMERGENCY`：提示立即急救或急诊
- `HIGH`：建议尽快线下就医
- `MEDIUM`：建议 24-48 小时内就医评估
- `LOW`：以观察和基础健康管理为主

### 4) 动态追问卡片
当信息不足时自动触发追问，逐步补全关键字段后重新评估，支持多轮补充。

### 5) 推荐科室与就医建议
结合风险等级与症状组合，给出建议就诊方向与下一步行动建议。

### 6) 免责声明与安全提示
在结果区域明确非诊断属性与急危重症应对提示，降低误用风险。

---

## 产品设计亮点

- **规则引擎负责风险等级和安全边界**：对高危信号进行确定性优先识别，避免单纯依赖 LLM
- **LLM 负责结构化与表达层**：承担症状结构化、解释生成、建议生成和追问生成
- **高危信号优先识别**：胸闷胸痛、呼吸困难、冷汗、意识异常等 Red Flag 优先进入高风险路径
- **低风险轻症保护**：避免将“流鼻涕、体温正常”等轻症输入误判为高危
- **多轮追问补全信息**：先补齐部位、时长、严重度、伴随症状，再做更稳健分层
- **Explainability 提升用户理解**：展示风险判定依据与模型解释，增强结果可读性

---

## Fallback 与鲁棒性设计

- **Layer 1：规则预筛**  
  对明显高危或低风险信号进行快速初步判断
- **Layer 2：LLM 语义分析**  
  完成复杂语义下的结构化提取、解释与建议生成
- **Layer 3：关键词回退**  
  当 LLM 调用异常时，使用关键词与规则路径提供保守结果

说明：该机制用于提升系统在异常场景下的可用性与连续性，不等同于医疗诊断可靠性保证。

---

## 技术架构图

```text
用户自然语言输入
    ↓
[输入处理与意图识别]
规则预筛 -> LLM 分类（DeepSeek） -> 关键词回退
    ↓
[风险引擎（规则优先）]
输出 LOW / MEDIUM / HIGH / EMERGENCY
    ↓
[LLM 生成层（DeepSeek）]
症状结构化 + Explainability + 就医建议 + 动态追问
    ↓
[前端展示层]
风险卡片 + 追问交互 + 解释面板 + 免责声明
```

**技术栈：**

- 前端：`Vite` + `React` + `Tailwind CSS`（部署：`Vercel`）
- 后端：`Python` + `FastAPI`（部署：`Railway`）
- LLM：`DeepSeek API`（OpenAI-compatible 调用）
- 风险分层：`规则引擎 + LLM 分析` 双层协同

---

## 测试用例（示例）

- `有点流鼻涕，体温正常` -> `LOW`
- `流鼻涕，轻微咳嗽，没有发烧` -> `LOW`
- `流鼻涕发烧38度` -> `MEDIUM`
- `头疼三天，昨晚发烧38.5度` -> `触发追问 / 非 LOW`
- `胸口像被压住，喘不上气，出冷汗` -> `HIGH / EMERGENCY`

---

## 本地运行

**环境要求：** `Python 3.10+`，`Node.js 18+`

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env  # 填入 LLM_API_KEY
uvicorn main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173`

---

## 项目边界

- 不替代医生诊断
- 不用于急救决策
- 仅用于健康信息初筛与产品 Demo 展示

---

## 关于作者

985 高校公共卫生专业研究生在读，本科信息与计算科学，求职方向为 AI 医疗 PM / AI 产品实习。

---

## 免责声明

本系统为演示用途，仅用于学习、研究与作品集展示，不构成医疗建议或诊断依据。  
如出现急危重症，请立即拨打 120 或前往线下急诊。
