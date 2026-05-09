# 🏗️ 系统架构设计文档

## 📐 整体架构

```
┌──────────────────────────────────────────────────────────────┐
│                        用户界面层                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  React SPA (Vite + Tailwind CSS)                    │    │
│  │  - 症状输入组件 (SymptomInput)                      │    │
│  │  - 风险卡片组件 (RiskCard)                         │    │
│  │  - 结果面板组件 (ResultPanel)                      │    │
│  │  - 追问面板组件 (FollowupPanel)                    │    │
│  │  - 导航栏组件 (Navbar)                            │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────┬──────────────────────────────────────┘
                        │ HTTP/JSON (CORS)
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                        API 网关层                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  FastAPI Application (main.py)                      │    │
│  │  - CORS 中间件                                      │    │
│  │  - 全局异常处理（确保永不返回500）                  │    │
│  │  - 请求/响应验证（Pydantic）                       │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                        业务逻辑层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ LLM Service  │  │ Risk Engine  │  │   Session    │      │
│  │              │  │              │  │   Manager    │      │
│  │ - 症状结构化 │  │ - 60+规则库 │  │ - 会话存储   │      │
│  │ - 分析生成   │  │ - 关键词匹配 │  │ - 超时管理   │      │
│  │ - 追问生成   │  │ - 正则规则   │  │ - 历史记录   │      │
│  │ - Prompt管理 │  │ - 风险评分   │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                        │                                      │
│                        ▼                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │          降级服务 (Fallback Service)                 │    │
│  │  - Layer 1: LLM失败 → 关键词提取                   │    │
│  │  - Layer 2: 规则失败 → 保守策略（MEDIUM）           │    │
│  │  - Layer 3: 全局异常 → 安全兜底                    │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                        外部服务层                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Anthropic Claude API                               │    │
│  │  - 模型: claude-sonnet-4-20250514                   │    │
│  │  - 超时: 30 秒                                      │    │
│  │  - 重试: 无（由降级机制处理）                       │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 核心流程

### 1. 主分析流程 (POST /api/analyze)

```
用户输入
   │
   ▼
┌─────────────────────┐
│  输入验证            │  Pydantic 模型验证
└─────────────────────┘
   │
   ▼
┌─────────────────────┐
│  症状结构化          │  LLM Stage 1
│  (LLM Service)       │  ├─ 提取症状列表
└─────────────────────┘  ├─ 识别持续时间
   │                     ├─ 判断严重程度
   │ StructuredSymptoms  ├─ 提取体温
   ▼                     └─ 发病方式
┌─────────────────────┐
│  风险评估            │  规则引擎（规则优先）
│  (Risk Engine)       │  ├─ 匹配 HIGH 规则
└─────────────────────┘  ├─ 匹配 MEDIUM 规则
   │                     ├─ 匹配 LOW 规则
   │ RiskAssessment      └─ 计算风险分数
   ▼
┌─────────────────────┐
│  分析生成            │  LLM Stage 2
│  (LLM Service)       │  ├─ 生成就诊建议
└─────────────────────┘  ├─ 推荐科室
   │                     ├─ 紧急程度时间线
   │ Analysis Result     ├─ 自然语言解释
   ▼                     └─ AI 推理过程
┌─────────────────────┐
│  追问生成            │  LLM Stage 3（可选）
│  (LLM Service)       │  ├─ 生成 1-2 个问题
└─────────────────────┘  ├─ 问题分类
   │                     ├─ 提供选项（可选）
   │ Followup Questions  └─ 风险等级判断
   ▼
┌─────────────────────┐
│  会话保存            │  Session Manager
│  (Session Manager)   │  ├─ 创建会话 ID
└─────────────────────┘  ├─ 保存分析结果
   │                     └─ 更新累积症状
   │
   ▼
┌─────────────────────┐
│  返回结果            │  AnalysisResult
└─────────────────────┘  └─ JSON 响应
```

### 2. 追问流程 (POST /api/followup)

```
追问回答
   │
   ▼
┌─────────────────────┐
│  会话验证            │  Session Manager
│  - 检查会话存在      │  ├─ session_id 验证
│  - 检查追问次数      │  ├─ 追问轮数检查
│  - 检查风险等级      │  └─ HIGH 不追问
└─────────────────────┘
   │
   ▼
┌─────────────────────┐
│  合并输入            │  原始输入 + 追问回答
│  "头疼三天..."       │  + "主要在前额"
│  + 追问回答          │  = 完整描述
└─────────────────────┘
   │
   ▼
┌─────────────────────┐
│  重新执行主流程      │  与 /api/analyze 相同
│  - 症状结构化        │  但 session_id 保持
│  - 风险评估          │  followup_round + 1
│  - 分析生成          │
└─────────────────────┘
   │
   ▼
┌─────────────────────┐
│  更新会话            │  Session Manager
│  - 记录 QA 对        │  ├─ 保存问答
│  - 更新风险等级      │  ├─ 累积症状
│  - 增加追问轮数      │  └─ 更新时间戳
└─────────────────────┘
   │
   ▼
┌─────────────────────┐
│  返回新结果          │  AnalysisResult
└─────────────────────┘  └─ followup_round 更新
```

---

## 🛡️ 降级策略详解

### Layer 1: LLM 失败降级

**触发条件**:
- Anthropic API 超时（> 30s）
- API 返回错误（401、429、500）
- JSON 解析失败
- 网络连接失败

**降级方案**:
```python
def create_fallback_structured(user_input: str) -> StructuredSymptoms:
    # 1. 关键词匹配症状
    symptoms = []
    for keyword in ["头痛", "发烧", "咳嗽", ...]:
        if keyword in user_input:
            symptoms.append(keyword)
    
    # 2. 正则提取体温
    temp_match = re.search(r'(\d{2}\.?\d?)\s*[度℃]', user_input)
    temperature = float(temp_match.group(1)) if temp_match else None
    
    # 3. 正则提取持续时间
    duration_match = re.search(r'(\d+)\s*[天日]', user_input)
    duration = duration_match.group(0) if duration_match else "未知"
    
    # 4. 简单严重程度判断
    severity = "重度" if "严重" in user_input else "轻度"
    
    return StructuredSymptoms(...)
```

**用户体验**:
- 右上角显示"降级模式"黄色标签
- 处理速度更快（毫秒级）
- 风险评估仍然由规则引擎保证准确性

### Layer 2: 规则引擎失败降级

**触发条件**:
- 规则引擎代码异常
- 正则匹配错误
- 数据类型错误

**降级方案**:
```python
def create_fallback_risk() -> RiskAssessment:
    # 默认 MEDIUM 风险（保守策略）
    return RiskAssessment(
        level="MEDIUM",
        score=50,
        triggered_rules=["FALLBACK"],
        rule_explanations=["系统异常，建议就医以确保安全"]
    )
```

**原因**: 在不确定情况下，建议就医比建议自我观察更安全。

### Layer 3: 全局异常兜底

**触发条件**:
- 任何未捕获的 Python 异常
- 内存不足
- 服务器错误

**降级方案**:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # 永不返回 HTTP 500
    # 始终返回 HTTP 200 + 安全的降级数据
    fallback = create_safe_fallback_result(
        "",
        reason="服务器内部错误，已启用安全降级"
    )
    return JSONResponse(status_code=200, content=fallback.dict())
```

**关键设计**:
- **永不返回 HTTP 500** - 对用户友好
- **默认建议就医** - 安全优先
- **记录 fallback_reason** - 便于调试

---

## 📊 数据流转

### 请求数据流

```json
// 1. 前端发送
POST /api/analyze
{
  "user_input": "我头疼三天了，昨晚发烧38.5度",
  "session_id": null
}

// 2. Pydantic 验证
AnalyzeRequest(
  user_input: str (min_length=1, max_length=2000),
  session_id: Optional[str]
)

// 3. LLM 结构化
{
  "symptoms": ["头疼", "发烧"],
  "duration": "三天",
  "severity": "中度",
  "temperature": 38.5,
  "symptom_onset": "渐进"
}

// 4. 规则引擎评估
{
  "level": "MEDIUM",
  "score": 50,
  "triggered_rules": ["M001", "M004"],
  "rule_explanations": [
    "触发中危规则: 中等发热持续2天以上",
    "触发中危规则: 头痛持续48小时以上"
  ]
}

// 5. LLM 生成分析
{
  "advice": "建议在24-48小时内就诊...",
  "rationale": "根据发热程度和持续时间判断...",
  "explainability": "您的症状组合...",
  "recommended_department": "内科",
  "urgency_timeline": "24-48小时内"
}

// 6. 合并返回
{
  "session_id": "uuid-xxx",
  "structured": {...},
  "risk": {...},
  "advice": "...",
  "needs_followup": true,
  "followup_questions": [...],
  "processing_time_ms": 3420,
  "llm_used": true,
  "fallback_reason": null
}
```

---

## 🔐 安全设计

### 1. 输入验证

- **字符长度限制**: 1-2000 字符（防止超长输入）
- **类型校验**: Pydantic 严格类型检查
- **SQL 注入防护**: 无数据库操作（内存会话管理）
- **XSS 防护**: React 自动转义

### 2. API 安全

- **CORS 白名单**: 仅允许配置的前端域名
- **无认证**: 演示系统，生产环境需添加 JWT
- **速率限制**: 未实现（生产需添加）

### 3. 医疗安全

- **规则优先**: 风险等级由规则引擎决定，LLM 无权修改
- **保守策略**: 不确定时默认 MEDIUM 风险
- **明确免责**: 前端和 README 均显示免责声明
- **HIGH 不追问**: 避免延误紧急就医

### 4. 数据隐私

- **无持久化**: 会话数据存储在内存，重启即清空
- **30 分钟超时**: 自动清理过期会话
- **无日志记录**: 不记录用户输入（生产环境需考虑合规）

---

## 📈 性能优化

### 1. 后端优化

- **Async/Await**: LLM 调用使用异步，避免阻塞
- **规则引擎缓存**: 规则库在启动时加载，O(1) 查找
- **会话内存管理**: 定期清理超时会话（可配置）

### 2. 前端优化

- **Vite 构建**: HMR 热更新，生产打包优化
- **Tailwind CSS**: 仅打包使用的样式，体积小
- **组件懒加载**: 可按需加载（未实现，可扩展）
- **本地缓存**: 历史记录存储在 localStorage

### 3. LLM 调用优化

- **温度参数**: 结构化用 0.1（确定性），解释用 0.3（多样性）
- **Max Tokens 限制**: 
  - 结构化: 1024 tokens
  - 分析: 2048 tokens
  - 追问: 512 tokens
- **无流式输出**: 为简化实现，未使用 SSE（可扩展）

---

## 🧪 测试策略

### 1. 单元测试（未实现，建议添加）

```python
# tests/test_risk_engine.py
def test_high_risk_chest_pain():
    engine = RiskEngine()
    result = engine.evaluate("胸口像被压住一样疼，喘不上气", ...)
    assert result.level == "HIGH"
    assert "H001" in result.triggered_rules

def test_fallback_when_llm_fails():
    structured = create_fallback_structured("头疼")
    assert "头疼" in structured.symptoms
```

### 2. 集成测试（手动测试）

- 15 个 demo 案例全覆盖
- 追问系统多轮测试
- 降级模式测试（关闭 API Key）

### 3. 压力测试（未实现）

- 并发请求测试
- LLM 超时测试
- 内存泄漏测试

---

## 🚀 部署建议

### 1. 生产环境改进

- [ ] 使用 PostgreSQL/Redis 替代内存会话
- [ ] 添加 JWT 认证
- [ ] 实现速率限制（如 slowapi）
- [ ] 日志系统（Sentry、Logstash）
- [ ] 监控指标（Prometheus + Grafana）
- [ ] Docker 容器化
- [ ] CI/CD 自动化部署

### 2. Docker 部署（示例）

```dockerfile
# backend/Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]

# frontend/Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build
CMD ["npx", "serve", "-s", "dist", "-l", "5173"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  
  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
```

---

## 📚 扩展方向

### 1. 功能扩展

- [ ] 多语言支持（i18n）
- [ ] 语音输入（Whisper API）
- [ ] 图片识别（病灶、皮疹）
- [ ] 用户登录 + 病历管理
- [ ] 导出 PDF 报告
- [ ] 对接医院预约系统

### 2. AI 能力扩展

- [ ] 接入医学知识图谱（Neo4j）
- [ ] 多模型集成（GPT + Claude）
- [ ] Fine-tuning 医疗专用模型
- [ ] RAG（检索增强生成）
- [ ] Few-shot Learning（案例学习）

### 3. 商业化扩展

- [ ] 付费订阅（Stripe）
- [ ] 医生端管理后台
- [ ] 企业 API 接口
- [ ] 白标解决方案
- [ ] 数据分析看板

---

**文档版本**: v2.0  
**最后更新**: 2026-05-10  
**作者**: AI Product Engineer
