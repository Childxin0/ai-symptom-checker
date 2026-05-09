# 🚀 一键启动指南

## Windows 用户

### 第一步：配置 API Key

1. 打开 `backend\.env` 文件
2. 将 `ANTHROPIC_API_KEY=your_api_key_here` 替换为你的真实 API Key
3. 保存文件

**获取 API Key**：访问 [https://console.anthropic.com](https://console.anthropic.com)

---

### 第二步：启动后端

打开 PowerShell 终端：

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

看到以下输出表示成功：
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**保持这个终端打开！**

---

### 第三步：启动前端

打开 **新的** PowerShell 终端：

```powershell
cd frontend
npm run dev
```

看到以下输出表示成功：
```
VITE v5.4.21  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

---

### 第四步：访问系统

浏览器打开：`http://localhost:5173`

---

## macOS / Linux 用户

### 启动后端

```bash
cd backend
source venv/bin/activate  # Linux/macOS 使用 source
python main.py
```

### 启动前端

```bash
cd frontend
npm run dev
```

---

## 快速测试

### 方法 1：使用示例

1. 点击"填入示例"按钮
2. 点击"分析症状"
3. 等待 3-5 秒（真实 LLM 调用需要时间）
4. 查看右侧结果

### 方法 2：手动输入

尝试输入：
```
我头疼三天了，昨晚发烧38.5度，有点恶心，吃不下东西
```

预期结果：
- 风险等级：MEDIUM（橙色）
- 触发规则：M001、M004
- 建议：24-48小时内就医
- 推荐科室：内科
- **出现紫色追问面板**

### 方法 3：测试追问

在上一步基础上，回答追问问题，系统会重新评估风险。

---

## 常见问题

### Q: 后端启动失败，提示"找不到 anthropic"

**A**: 依赖未安装，运行：
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Q: 前端启动失败，提示"找不到 vite"

**A**: 依赖未安装，运行：
```powershell
cd frontend
npm install
```

### Q: 分析时报错"未配置 ANTHROPIC_API_KEY"

**A**: 检查 `backend\.env` 文件：
1. 确保文件名是 `.env`（不是 `.env.example`）
2. 确保 `ANTHROPIC_API_KEY=` 后面填写了真实的 API Key
3. 重启后端服务

### Q: 分析速度很慢（超过 10 秒）

**A**: 正常现象，Claude API 调用需要 3-8 秒。如果超过 30 秒，可能是：
- 网络问题（Claude 服务器在国外）
- API 额度不足
- API Key 无效

系统会自动降级，仍然返回结果。

### Q: 想看降级模式的效果

**A**: 
1. 停止后端
2. 在 `backend\.env` 中将 `ANTHROPIC_API_KEY=` 设置为空字符串
3. 重启后端
4. 分析任意症状，右上角会显示"降级模式"黄色标签
5. 系统仍然能正常工作，但使用关键词匹配代替 LLM

---

## API 测试

### 使用 curl

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "我头疼三天了，昨晚发烧38.5度"
  }'
```

### 使用 Postman

1. Method: POST
2. URL: `http://localhost:8000/api/analyze`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "user_input": "我头疼三天了，昨晚发烧38.5度"
}
```

### 访问 API 文档

浏览器打开：`http://localhost:8000/docs`

Swagger UI 会自动生成交互式 API 文档。

---

## 停止服务

### 停止后端
在后端终端按 `Ctrl + C`

### 停止前端
在前端终端按 `Ctrl + C`

---

**祝你使用愉快！🎉**

如有问题，请查看 `README.md` 或 `DEMO_GUIDE.md`
