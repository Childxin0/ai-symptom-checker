# 🏥 AI 症状结构化 + 风险分层系统

> **商业级医疗 AI 初筛 MVP** · 对标 ADA Health & Buoy Health

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![Anthropic Claude](https://img.shields.io/badge/Anthropic-Claude%20Sonnet%204-purple.svg)](https://anthropic.com)

---

## 📸 项目展示

### 主界面（左右布局）
```
┌─────────────────────────────────────────────────┐
│  Logo     AI 症状初筛         免责声明    GitHub │
├───────────────┬─────────────────────────────────┤
│               │                                 │
│  症状输入区   │    风险评估卡片（带动画）      │
│  - 字数统计   │    ├─ HIGH: 红色+脉冲动画      │
│  - 示例填充   │    ├─ MEDIUM: 橙色              │
│  - 历史记录   │    └─ LOW: 绿色                 │
│               │                                 │
│               │    追问系统（紫色渐变卡片）    │
│               │    ├─ 多轮追问（最多3轮）       │
│               │    ├─ 选项式/文本式回答         │
│               │    └─ 进度指示                  │
│               │                                 │
│               │    结果详情面板                 │
│               │    ├─ 识别的症状（标签云）      │
│               │    ├─ 就诊建议（渐变卡片）      │
│               │    ├─ 推荐科室                  │
│               │    └─ 可解释性面板（可折叠）    │
│               │                                 │
└───────────────┴─────────────────────────────────┘
```

### 核心特性亮点

✅ **真实 LLM 调用** - Anthropic Claude Sonnet 4（两阶段 Pipeline）  
✅ **60+ 医疗规则** - 高中低三级风险分层，规则优先策略  
✅ **多轮追问系统** - 智能追问，完善症状信息（最多 3 轮）  
✅ **三层降级机制** - LLM 失败 → 规则引擎 → 安全兜底，永不返回 500  
✅ **商业级 UI/UX** - 对标 ADA Health，响应式设计，骨架屏加载  
✅ **可解释 AI** - 触发规则透明展示，AI 推理过程可追溯  
✅ **会话管理** - 支持多轮对话，30 分钟会话超时

---

## 🏗️ 系统架构

```
                 ┌─────────────────────┐
                 │   React Frontend    │
                 │  (Vite + Tailwind)  │
                 └──────────┬──────────┘
                            │ /api/*
                            ▼
                 ┌─────────────────────┐
                 │   FastAPI Backend   │
                 │    (Python 3.10+)   │
                 └──────────┬──────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
  │ LLM Service  │  │ Risk Engine │  │   Session    │
  │  (Claude)    │  │ (60+ Rules) │  │   Manager    │
  └──────────────┘  └─────────────┘  └──────────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Fallback Service   │
                 │  (3-Layer Safety)   │
                 └─────────────────────┘
```

### 技术栈

**后端 (Backend)**
- **框架**: FastAPI 0.115+
- **LLM**: Anthropic Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- **数据验证**: Pydantic V2
- **异步**: Async/Await
- **规则引擎**: 自研 60+ 医疗规则（关键词+正则+阈值）

**前端 (Frontend)**
- **框架**: React 18
- **构建**: Vite 5
- **样式**: Tailwind CSS 3
- **UI组件**: 自研组件库（对标 ADA Health）
- **动画**: CSS + Tailwind Animations

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Anthropic API Key（[获取地址](https://console.anthropic.com)）

### 1️⃣ 克隆项目

```bash
git clone https://github.com/your-repo/AI-Symptom-Structuring-Risk-Layering.git
cd AI-Symptom-Structuring-Risk-Layering
```

### 2️⃣ 配置后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 ANTHROPIC_API_KEY
```

**.env 配置说明**
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx     # ⚠️ 必填：Anthropic API Key
ANTHROPIC_MODEL=claude-sonnet-4-20250514
ANTHROPIC_TIMEOUT=30.0

API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

MAX_FOLLOWUP_ROUNDS=3              # 最多追问轮数
SESSION_TIMEOUT_MINUTES=30         # 会话超时时间
```

### 3️⃣ 启动后端

```bash
# 在 backend/ 目录下
python main.py
```

后端将运行在 `http://localhost:8000`

**API 文档**: `http://localhost:8000/docs` （Swagger UI）

### 4️⃣ 启动前端

```bash
# 打开新终端，在项目根目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 `http://localhost:5173`

### 5️⃣ 访问系统

浏览器打开：`http://localhost:5173`

---

## 🎯 核心功能演示

### 1. 症状结构化（第一阶段 LLM）

**输入**
```
我头疼三天了，昨晚发烧38.5度，有点恶心，吃不下东西
```

**输出（内部结构化数据）**
```json
{
  "symptoms": ["头疼", "发烧", "恶心", "食欲不振"],
  "duration": "三天",
  "severity": "中度",
  "temperature": 38.5,
  "symptom_onset": "渐进"
}
```

### 2. 风险评估（规则引擎优先）

**规则引擎触发**
```
M001: 中等发热持续2天以上
M004: 头痛持续48小时以上
M007: 反复呕吐/恶心
→ 风险等级: MEDIUM (50/100)
```

### 3. 第二阶段 LLM 生成建议

```json
{
  "advice": "建议在24-48小时内就诊...",
  "recommended_department": "内科",
  "urgency_timeline": "24-48小时内",
  "explainability": "您的症状组合（发热+头痛+恶心）持续3天，触发了中等风险规则...",
  "rationale": "根据发热程度和持续时间判断..."
}
```

### 4. 多轮追问系统

**首次分析后追问**
```
Q1: 头痛的部位主要在哪里？
    选项: [前额, 两侧太阳穴, 整个头部]
    
Q2: 恶心是否伴随呕吐？
    选项: [只恶心不吐, 偶尔吐, 频繁呕吐]
```

**用户回答后重新评估**
```
用户选择：前额 + 频繁呕吐
→ 风险等级可能从 MEDIUM → HIGH
→ 建议更新为"立即就医"
```

---

## 📡 API 接口文档

### POST `/api/analyze` - 主分析接口

**请求**
```json
{
  "user_input": "我头疼三天了，昨晚发烧38.5度",
  "session_id": null  // 可选，首次调用传 null
}
```

**响应**
```json
{
  "session_id": "uuid-xxxx",
  "timestamp": "2026-05-10T00:00:00",
  "structured": {
    "symptoms": ["头疼", "发烧"],
    "duration": "三天",
    "severity": "中度",
    "temperature": 38.5
  },
  "risk": {
    "level": "MEDIUM",
    "score": 50,
    "triggered_rules": ["M001", "M004"],
    "rule_explanations": [
      "触发中危规则: 中等发热持续2天以上",
      "触发中危规则: 头痛持续48小时以上"
    ]
  },
  "advice": "建议在24-48小时内就诊...",
  "recommended_department": "内科",
  "urgency_timeline": "24-48小时内",
  "explainability": "您的症状组合...",
  "needs_followup": true,
  "followup_questions": [
    {
      "question": "头痛的部位主要在哪里？",
      "category": "location",
      "options": ["前额", "两侧太阳穴", "整个头部"]
    }
  ],
  "followup_round": 0,
  "processing_time_ms": 3420,
  "llm_used": true,
  "fallback_reason": null
}
```

### POST `/api/followup` - 追问接口

**请求**
```json
{
  "session_id": "uuid-xxxx",
  "followup_answer": "前额",
  "question_index": 0
}
```

**响应**
```
与 /api/analyze 相同，但 followup_round 递增
```

### GET `/api/health` - 健康检查

**响应**
```json
{
  "status": "ok",
  "llm_available": true,
  "model": "claude-sonnet-4-20250514"
}
```

---

## 🛡️ 安全与降级策略

### 三层降级机制

```
Layer 1: LLM 失败 → 规则引擎 + 关键词提取
         ├─ API 超时/限流
         └─ JSON 解析失败
         
Layer 2: 规则引擎失败 → 保守策略（默认 MEDIUM 风险）
         └─ 正则匹配异常
         
Layer 3: 全局异常 → 安全兜底响应
         ├─ 永不返回 HTTP 500
         ├─ 默认建议"尽快就医"
         └─ 标记 fallback_reason
```

### 规则优先策略

```python
# 风险等级由规则引擎决定，LLM 仅增强解释性
risk_level = rules.evaluate(user_input, structured_data)  # 规则优先

if llm_available:
    rationale = llm.explain_risk(structured_data, risk_level)  # LLM 补充
else:
    rationale = fallback.explain_risk(risk_level)  # 降级解释
```

---

## 📊 演示案例（15 个）

### HIGH 风险案例（5 个）

| ID | 症状描述 | 触发规则 |
|----|----------|----------|
| 1  | 胸口像被压住一样疼，喘不上气，出了很多冷汗 | H001 |
| 2  | 突然剧烈头痛，这是我一生中最严重的一次 | H004 |
| 3  | 右侧身体突然没力气，说话也不清楚了 | H006, H008 |
| 4  | 吃了海鲜后全身起红疹，喉咙肿胀 | H017, H018 |
| 5  | 怀孕5个月，今天突然肚子很痛，还有阴道出血 | H019 |

### MEDIUM 风险案例（5 个）

| ID | 症状描述 | 触发规则 |
|----|----------|----------|
| 6  | 头疼三天了，昨晚发烧38.5度 | M001, M004 |
| 7  | 肚子痛了快8小时了，主要是右下腹 | M005, M006 |
| 8  | 心跳很快，感觉心慌，有点胸闷 | M010 |
| 9  | 从昨天开始一直吐，吃什么吐什么 | M007 |
| 10 | 我有高血压，最近头疼得厉害 | M011 |

### LOW 风险案例（5 个）

| ID | 症状描述 | 触发规则 |
|----|----------|----------|
| 11 | 有点累，鼻塞流鼻涕，应该是感冒了 | L002 |
| 12 | 头有点疼但不严重，可能是昨晚没睡好 | L001 |
| 13 | 胃有点胀气，吃完饭后感觉消化不良 | L005 |
| 14 | 最近工作压力大，有点失眠 | L004 |
| 15 | 眼睛干涩，看电脑太久了 | DEFAULT |

---

## 💡 技术亮点（面试话术）

### 1. AI 产品设计能力

> "采用两阶段 LLM Pipeline 设计：先用 Claude 做症状结构化（提取关键信息），再用规则引擎做风险判定（确保医疗安全），最后用 LLM 生成自然语言解释。这种架构既保证了准确性（规则优先），又提升了用户体验（自然语言解释）。"

### 2. 医疗 AI 安全意识

> "实现了三层降级机制：LLM 失败时切换到规则引擎，规则引擎失败时返回保守策略，全局异常时返回安全兜底。整个系统永不返回 HTTP 500，确保用户始终能得到有效建议。在不确定情况下，默认建议尽快就医，符合医疗场景的安全优先原则。"

### 3. Prompt Engineering

> "针对医疗场景设计了分层 Prompt：System Prompt 定义 AI 角色（医疗初筛助手），Structure Prompt 要求严格 JSON 输出，Risk Control Prompt 强调不做诊断。在追问环节，Prompt 要求生成 1-2 个关键问题，并根据风险等级动态调整追问策略（HIGH 不追问，直接建议就医）。"

### 4. UX 设计理念

> "对标 ADA Health 的商业级 UI：左右布局区分输入和输出、HIGH 风险用脉冲动画吸引注意、加载时显示步骤进度（识别症状→风险评估→生成建议）、追问系统支持选项式和文本式两种交互、可解释性面板可折叠展示触发规则。所有交互细节都围绕'降低用户焦虑，提升信任感'设计。"

### 5. 工程化能力

> "后端使用 FastAPI + Pydantic 确保 API 类型安全，前端使用 React + Tailwind 实现快速迭代。项目结构清晰：core/ 核心业务逻辑，api/ 路由层，models/ 数据模型，components/ UI 组件。支持 Docker 一键部署，环境变量管理规范，代码注释完善。"

---

## 🎓 适用场景

✅ **AI PM 求职作品集** - 展示 AI 产品设计、Prompt Engineering、UX 设计能力  
✅ **医疗 AI 原型** - 可扩展为真实医疗初筛系统（需接入医学知识库）  
✅ **技术面试 Demo** - 涵盖前后端、AI、产品多个维度  
✅ **AI 应用学习** - 学习 LLM + 规则引擎混合架构、多轮对话系统

---

## 📝 免责声明

⚠️ **本项目仅用于技术演示和学习交流，不构成任何医疗建议。**

- 不能替代专业医疗诊断
- 分析结果仅供参考，不作为就医依据
- 如有严重或紧急症状，请立即拨打 120 或前往急诊
- 使用者需对自己的医疗决策负责

---

## 📜 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 👨‍💻 作者

**AI Product Engineer**  
📧 Email: your-email@example.com  
🔗 LinkedIn: [Your Profile](https://linkedin.com/in/your-profile)  
💼 Portfolio: [Your Website](https://your-website.com)

---

## 🙏 致谢

- [Anthropic Claude](https://anthropic.com) - LLM 能力提供
- [ADA Health](https://ada.com) & [Buoy Health](https://buoyhealth.com) - UI/UX 设计灵感
- [FastAPI](https://fastapi.tiangolo.com) - 后端框架
- [React](https://react.dev) & [Tailwind CSS](https://tailwindcss.com) - 前端技术栈

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
