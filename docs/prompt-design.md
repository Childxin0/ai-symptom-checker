# Prompt 设计

## 文件分层（`prompts/`）

| 文件 | 作用 |
| --- | --- |
| `system.txt` | 角色边界：非执业医师、结构化助手、急症红线、禁止诊断与处方。 |
| `structured-output.txt` | JSON Schema 契约、`ai_rationale` 字段用于审计链。 |
| `risk-control.txt` | 模型侧自检清单；声明服务端将做一致性复核与安全合并。 |

## 调用方式（后端）

`backend/src/openaiClient.js` 将 **structured-output + risk-control** 作为用户消息体的一部分，**system** 单独作为 system 消息；使用 `response_format: { type: "json_object" }` 强化结构化输出。

## 与 PM 工作的映射

- **可迭代**：提示词与关键词表解耦，便于 A/B 与回归测试。
- **可审计**：`ai_rationale` 留在服务端结构化链路；终端用户仅看到 `presenter` 拼装的自然语言解释。
- **可降级**：无 Key 时服务端启用离线路径，对外 API 形态保持一致。

## 环境变量

- `OPENAI_API_KEY`：启用完整 LLM 路径。
- `OPENAI_MODEL`：默认 `gpt-4o-mini`，可按成本与效果调整。
