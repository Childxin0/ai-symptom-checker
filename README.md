# AI症状初筛系统 - 产品化医疗Triage系统

> 一个基于LLM + 规则引擎的AI医疗症状初筛系统，具备输入意图识别、症状结构化、风险分层、追问机制、降级容错的完整产品化能力。

**定位**：AI PM / AI医疗PM 作品集项目  
**技术栈**：FastAPI + Claude Sonnet 4.5 + React + Tailwind CSS  
**测试状态**：✅ 9/9 测试通过（100%）  

---

## 项目定位

这**不是**一个简单的医疗聊天机器人，而是一个**产品化的医疗初筛系统（Medical Triage System）**，核心设计理念：

1. **输入意图识别**：区分非医疗输入、信息不足、有效症状，避免系统误用
2. **规则优先风险分层**：急症Red Flag必须识别，规则引擎保底，LLM辅助
3. **追问机制**：信息不足时不盲目判低风险，标准化追问收集关键信息
4. **Fallback降级**：LLM失败时，规则+关键词匹配仍能提供基本服务
5. **可解释性**：显示触发规则和推理过程，增强用户信任

---

## 用户路径

```
用户输入症状描述
      ↓
【输入意图识别层】
      ↓
   ├─→ 非医疗输入 → 警告提示，引导正确使用
   ├─→ 信息不足 → 追问问题，收集关键信息
   └─→ 有效症状
            ↓
      【症状结构化】
      LLM提取：症状、时间、体温、严重程度
            ↓
      【规则优先风险分层】
      规则引擎评估 → EMERGENCY/HIGH/MEDIUM/LOW
            ↓
      【生成建议与解释】
      LLM生成：就诊建议、推荐科室、解释说明
            ↓
      【前端展示】
      风险卡片、症状识别、追问、可解释性
```

---

## 系统架构

### 后端架构（FastAPI）

```
api/routes.py
    ↓
input_validator.py（输入意图识别）
    ↓
├─→ non_medical_input → 返回警告
├─→ insufficient_symptom → 返回追问
└─→ valid_symptom
        ↓
    llm_service.py（症状结构化）
        ↓
    risk_engine.py（规则优先风险分层）
        ↓
    llm_service.py（生成分析和建议）
        ↓
    AnalysisResult（返回前端）
```

**降级容错**：
- LLM失败 → `fallback.py`（关键词匹配 + 规则引擎）
- 规则引擎失败 → 保守评估（MEDIUM）
- 全部失败 → 安全降级（建议就医）

### 前端架构（React）

```
App.jsx
    ↓
├─→ SymptomInput（输入框）
├─→ RiskCard（风险卡片，仅valid_symptom显示）
├─→ ResultPanel
    ├─→ non_medical_input → 琥珀色警告卡
    ├─→ insufficient_symptom → 蓝色追问卡
    └─→ valid_symptom → 完整分析面板
└─→ FollowupPanel（仅valid_symptom + needs_followup显示）
```

**状态管理**：三种`input_type`完全互斥，无状态残留

---

## 核心功能模块

### 1. 输入意图识别（Input Validation）

**文件**：`backend/core/input_validator.py`

**功能**：区分三种输入状态

| 状态 | 判断条件 | 系统行为 |
|------|---------|---------|
| `non_medical_input` | 包含非医疗关键词（项目、代码、简历等） | 警告提示，不评估风险 |
| `insufficient_symptom` | 包含健康关注但信息不足（< 10字或无细节） | 触发追问，不评估风险 |
| `valid_symptom` | 包含症状词 + 细节，或紧急症状关键词 | 进入完整分析流程 |

**关键词库**：
- 非医疗关键词：50+（技术、职业、学习等）
- 症状关键词：40+（疼痛、发热、咳嗽等）
- 紧急症状关键词：15+（车祸、大出血、昏迷等）
- 健康关注词：10+（不舒服、难受、不适等）

**测试结果**：6/6通过（非医疗3个，信息不足3个）

---

### 2. 症状结构化（Symptom Structuring）

**文件**：`backend/core/llm_service.py`

**功能**：将自然语言转为结构化数据

**输入示例**：
```
"头疼三天，昨晚发烧38.5度，还有点恶心"
```

**输出结构**：
```json
{
  "symptoms": ["头疼", "发烧", "恶心"],
  "duration": "三天",
  "temperature": 38.5,
  "severity": "中度",
  "body_location": "头部",
  "symptom_onset": "渐进",
  "accompanying_symptoms": ["恶心"]
}
```

**技术方案**：
- LLM：Claude Sonnet 4.5（温度0.1，确保稳定输出）
- Prompt工程：明确要求完整症状识别、时间提取、体温数值
- 输出验证：Pydantic V2严格校验
- Fallback：关键词匹配 + 正则提取

**测试结果**：症状识别100%，duration提取100%（"三天"、"昨晚"等）

---

### 3. Red Flag风险分层（Risk Layering）

**文件**：`backend/core/risk_engine.py`

**设计理念**：**规则优先（Rules-First）**

#### 风险等级

| 等级 | 分数范围 | 建议时间线 | 示例 |
|------|---------|-----------|------|
| `EMERGENCY` | 85-100 | 立即 | 车祸外伤、大出血、呼吸困难、昏迷 |
| `HIGH` | 70-84 | 今日内 | 剧烈胸痛、持续高热、急腹症 |
| `MEDIUM` | 40-69 | 24-48小时 | 发烧头疼恶心、持续咳嗽 |
| `LOW` | 0-39 | 可观察 | 轻微感冒、流鼻涕 |

#### Red Flag规则体系（70+条）

**9大高危类别**：
1. 外伤与出血（车祸、大出血、止不住血）
2. 呼吸系统（呼吸困难、窒息、气短）
3. 神经系统（昏迷、抽搐、意识不清）
4. 急腹症（剧烈腹痛、肠梗阻）
5. 心血管（胸痛、心梗、压榨感）
6. 重度感染（高热+寒战、脓毒症）
7. 心理危机（自杀倾向、暴力倾向）
8. 中毒（误服、农药、煤气）
9. 儿科/产科急症（婴儿窒息、产后大出血）

**规则示例**：
```python
{
    "id": "TRAUMA_001",
    "keywords": ["车祸", "撞", "交通事故"],
    "level": "EMERGENCY",
    "score_boost": 100,
    "explanation": "交通事故可能导致内脏损伤或颅脑外伤"
}
```

**评分机制**：
- 基础分：根据症状组合
- 规则加成：触发Red Flag +15~100分
- 时间修正：持续时间越长 +5~15分
- 严重程度修正：重度 +10~20分
- 多症状叠加：+5~15分

**测试结果**：
- 车祸大出血 → EMERGENCY/100 ✅
- 发烧头疼恶心 → MEDIUM/64 ✅
- 轻微感冒 → LOW/20 ✅

---

### 4. Follow-up追问机制

**文件**：`backend/api/routes.py` + `frontend/src/components/ResultPanel.jsx`

**触发条件**：`input_type = insufficient_symptom`

**标准追问问题**（4个）：
1. 请描述具体的不适部位（如：头部、胸部、腹部等）
2. 症状持续了多久？（如：几小时、几天、几周）
3. 症状的严重程度如何？（如：轻微、中等、严重）
4. 是否有其他伴随症状？（如：发热、恶心、头晕等）

**产品设计**：
- 不显示风险卡片（避免误判低风险）
- 蓝色信息卡展示追问问题
- 引导用户在输入框补充信息后重新提交

**测试结果**：3/3触发追问，无误判低风险

---

### 5. Fallback降级机制

**文件**：`backend/core/fallback.py`

**三层降级策略**：

#### Layer 1：LLM症状结构化失败
→ 使用关键词匹配 + 正则提取
→ 症状库：30+常见症状
→ duration：正则提取"N天/小时/周"

#### Layer 2：规则引擎评估（Rules-only）
→ 基于Layer 1提取的症状
→ 规则匹配仍能识别高危场景
→ 保守评分

#### Layer 3：全部失败
→ 默认MEDIUM（保守策略）
→ 建议"24-48小时内就医"
→ 不低估风险

**测试验证**：
- 关闭LLM → 规则引擎仍能识别"大出血" → EMERGENCY ✅
- 规则引擎失败 → 降级为MEDIUM而非LOW ✅

---

### 6. Explainability可解释性

**文件**：`backend/core/risk_engine.py` + `frontend/src/components/ResultPanel.jsx`

**展示内容**：
1. 触发的规则ID和解释（中文）
2. AI分析过程（rationale）
3. 风险判断依据

**示例**（车祸大出血）：
```
触发的规则：
✓ 检测到交通事故外伤
✓ 检测到大量出血
✓ 检测到止血困难

AI分析过程：
用户描述了车祸导致的头部撞击和持续出血，
这是典型的紧急外伤场景，需要立即医疗干预...
```

**产品价值**：
- 增强用户信任
- 便于医生审核
- 方便系统调试

---

## 测试结果摘要

**测试文件**：`backend/test_state_conflict_fix.py`  
**测试报告**：`TEST_REPORT.md`  

| 测试类型 | 用例数 | 通过 | 失败 | 通过率 |
|---------|-------|------|------|--------|
| 非医疗输入 | 3 | 3 | 0 | 100% |
| 信息不足 | 3 | 3 | 0 | 100% |
| 有效症状 | 3 | 3 | 0 | 100% |
| **总计** | **9** | **9** | **0** | **100%** |

**关键测试场景**：
- ✅ 非医疗输入不进入风险评估
- ✅ 信息不足触发追问，不误判低风险
- ✅ 轻症识别为LOW（20分）
- ✅ 中症识别为MEDIUM（64分）
- ✅ 急症识别为EMERGENCY（100分）
- ✅ 症状识别准确（包括"流鼻涕"等常见症状）
- ✅ duration提取准确（"三天"、"昨晚"等）

**前端构建**：
```bash
npm run build
✓ 39 modules transformed.
✓ built in 2.10s
```
**状态**：✅ 无错误，无警告

---

## 已知限制

### 技术限制
1. **LLM依赖**：症状结构化依赖Claude API，需API Key和网络连接
2. **中文专用**：仅支持中文输入，未实现多语言
3. **单轮分析**：追问后需用户手动重新提交，未实现多轮对话记忆
4. **规则维护**：Red Flag规则需医疗专家持续审核和更新

### 产品限制
1. **非诊断工具**：仅为初筛，不能替代医生诊断
2. **未经认证**：为演示系统，未经医疗资质认证
3. **免责声明**：不可用于真实诊疗场景
4. **数据隐私**：未实现用户数据脱敏和隐私保护

---

## 本地运行

### 环境要求
- Python 3.11+
- Node.js 20+
- Claude API Key（需自行申请）

### 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
# 创建 .env 文件，添加：
# ANTHROPIC_API_KEY=your_api_key_here

# 4. 启动服务
uvicorn main:app --reload

# 后端运行在 http://localhost:8000
```

### 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 前端运行在 http://localhost:5173
```

### 访问系统

打开浏览器访问：`http://localhost:5173`

---

## 测试方式

### 自动化测试

```bash
cd backend

# 运行完整测试套件
python test_state_conflict_fix.py

# 预期输出：9 passed, 0 failed
```

### 手动测试

**测试用例建议**：

1. **非医疗输入**：`"帮我写简历"`
   - 预期：琥珀色警告，无风险卡

2. **信息不足**：`"不舒服"`
   - 预期：蓝色追问卡，4个问题

3. **轻症感冒**：`"有点流鼻涕，轻微咳嗽，体温正常"`
   - 预期：LOW/20分，绿色卡片

4. **中度症状**：`"头疼三天，发烧38.5度，恶心"`
   - 预期：MEDIUM/64分，黄色卡片

5. **紧急外伤**：`"被车撞了，大出血"`
   - 预期：EMERGENCY/100分，深红色脉冲卡片

---

## 技术栈

### 后端
- **框架**：FastAPI 0.115+
- **LLM**：Anthropic Claude Sonnet 4.5
- **数据验证**：Pydantic V2
- **Python版本**：3.11+

### 前端
- **框架**：React 18 + Vite 5
- **UI库**：Tailwind CSS 3
- **状态管理**：React Hooks
- **HTTP客户端**：Fetch API

### 部署（可选）
- **后端**：Vercel / Railway / Render
- **前端**：Vercel / Netlify / Cloudflare Pages

---

## 项目结构

```
.
├── backend/
│   ├── api/routes.py              # API路由
│   ├── core/
│   │   ├── input_validator.py     # 输入意图识别
│   │   ├── llm_service.py         # LLM服务
│   │   ├── risk_engine.py         # 风险分层引擎
│   │   ├── fallback.py            # 降级机制
│   │   └── models.py              # 数据模型
│   ├── test_state_conflict_fix.py # 自动化测试
│   └── requirements.txt           # Python依赖
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── RiskCard.jsx       # 风险卡片
│   │   │   ├── ResultPanel.jsx    # 结果面板
│   │   │   └── SymptomInput.jsx   # 输入组件
│   │   ├── App.jsx                # 主应用
│   │   └── api.js                 # API调用
│   └── package.json               # Node依赖
│
├── TEST_REPORT.md                 # 测试报告
├── DEMO_SCRIPT.md                 # 演示脚本
├── PORTFOLIO_SUMMARY.md           # 作品集总结
├── INTERVIEW_QA.md                # 面试问答
└── README.md                      # 本文件
```

---

## 部署指南（Vercel + Railway/Render）

### 前置准备

1. 确认 `.env` 已加入 `.gitignore`（已配置 ✅）
2. 复制 `backend/.env.example` 为 `backend/.env`，填写 `ANTHROPIC_API_KEY`

---

### 第一步：部署后端

选择以下任一平台：

#### 方案 A：Railway（推荐）
1. 访问 [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. 选择本仓库，设置 Root Directory 为 `backend`
3. 添加环境变量：
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   CORS_ORIGINS=https://your-app.vercel.app
   ```
4. 启动命令（Railway 自动检测，或手动设置）：
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. 记录分配到的后端地址，例如：`https://your-backend.up.railway.app`

#### 方案 B：Render
1. 访问 [render.com](https://render.com) → New → Web Service
2. 连接 GitHub 仓库，Root Directory 设为 `backend`
3. 启动命令：`uvicorn main:app --host 0.0.0.0 --port $PORT`
4. 添加环境变量（同上）

---

### 第二步：部署前端（Vercel）

1. 访问 [vercel.com](https://vercel.com) → New Project → 导入 GitHub 仓库
2. 配置构建设置：
   | 设置项 | 值 |
   |--------|-----|
   | Framework Preset | Vite |
   | Root Directory | `frontend` |
   | Build Command | `npm run build` |
   | Output Directory | `dist` |
3. 添加环境变量：
   ```
   VITE_API_BASE_URL=https://your-backend.up.railway.app
   ```
4. 点击 Deploy

---

### 第三步：配置后端 CORS

部署完成后，将 Vercel 分配的前端域名更新到后端环境变量：
```
CORS_ORIGINS=https://your-app.vercel.app
```

在 Railway/Render 控制台更新该变量后，后端会自动重启生效。

---

### 本地开发启动

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env          # 填写 ANTHROPIC_API_KEY
uvicorn main:app --reload

# 前端（新开终端）
cd frontend
npm install
npm run dev
```

本地开发时 **不需要** 设置 `VITE_API_BASE_URL`，Vite 代理自动将 `/api` 转发至 `localhost:8000`。

---

## 免责声明

⚠️ **重要提示**

1. **非医疗诊断工具**：本系统为技术演示项目，仅供学习和作品集展示使用
2. **不能替代医生**：任何症状评估结果不能替代专业医生的诊断
3. **急危重症**：如遇急危重症，请立即拨打120或前往医院急诊
4. **数据安全**：演示环境，未实现数据加密和隐私保护
5. **医疗合规**：未经过医疗资质认证，不得用于真实医疗场景
6. **风险自负**：使用本系统产生的任何后果，开发者不承担责任

---

## 联系方式

**项目作者**：AI PM候选人  
**项目定位**：AI医疗PM作品集项目  
**技术栈**：FastAPI + Claude + React  
**测试状态**：✅ 9/9 通过（100%）  

**相关文档**：
- 📊 [TEST_REPORT.md](./TEST_REPORT.md) - 详细测试报告
- 🎬 [DEMO_SCRIPT.md](./DEMO_SCRIPT.md) - 面试演示脚本
- 📝 [PORTFOLIO_SUMMARY.md](./PORTFOLIO_SUMMARY.md) - 作品集总结
- 💬 [INTERVIEW_QA.md](./INTERVIEW_QA.md) - 面试问答

---

**最后更新**：2026-05-10  
**版本**：v1.0.0  
**License**：MIT（仅供学习和作品集使用）  
