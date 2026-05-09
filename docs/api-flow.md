# API 流程

## `POST /api/analyze`

面向终端用户的产品化响应（不含调试字段、原始 JSON 契约或内部规则明细）。

**请求体**

```json
{ "text": "用户症状自然语言" }
```

（兼容字段 `symptom_text`。）

**成功响应（示例结构）**

```json
{
  "success": true,
  "risk": {
    "level": "MEDIUM",
    "headline": "中风险",
    "badge": "建议尽快就诊",
    "accent": "medium"
  },
  "guidance": {
    "summary": "面向用户的建议动作（自然语言）"
  },
  "insight": {
    "narrative": "为什么给出该分层的自然语言解释"
  },
  "profile": {
    "symptomFocus": ["头痛", "恶心"],
    "duration": "未知或未描述",
    "severity": "未知",
    "departmentHint": "神经内科"
  }
}
```

> `accent` 取值：`low` | `medium` | `high`，供前端主题样式映射（绿 / 黄 / 红）。

**服务不可用或未知异常（仍返回 200 + 可渲染结构）**

```json
{
  "success": false,
  "risk": { "level": "MEDIUM", "headline": "中风险", "badge": "评估未完成", "accent": "medium" },
  "guidance": { "summary": "…" },
  "insight": { "narrative": "…" },
  "profile": null
}
```

内部结构化字段（symptoms / duration / severity / risk_level / advice / ai_rationale 等）仍在服务端用于编排与自然语言生成，不以此形态直接暴露给前端。

## `GET /api/health`

```json
{ "status": "ok" }
```
