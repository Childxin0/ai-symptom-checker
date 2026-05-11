/**
 * API 调用封装 - 商业级标准
 */

// 本地开发：VITE_API_BASE_URL 为空，使用 Vite proxy（/api → localhost:8000）
// 生产部署：在 Vercel 环境变量中设置 VITE_API_BASE_URL=https://your-backend.railway.app
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE = `${BASE_URL}/api`;

// 调试：打开浏览器控制台可看到实际请求地址
console.log('[API] BASE_URL =', BASE_URL || '(empty → using Vite proxy)');
console.log('[API] API_BASE =', API_BASE);

/**
 * 分析症状
 */
export async function analyzeSymptoms(userInput, sessionId = null) {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_input: userInput,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '分析失败');
  }

  return await response.json();
}

/**
 * 回答追问
 */
export async function answerFollowup(sessionId, followupAnswer, questionIndex) {
  const response = await fetch(`${API_BASE}/followup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      followup_answer: followupAnswer,
      question_index: questionIndex,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '追问失败');
  }

  return await response.json();
}

/**
 * 健康检查
 */
export async function healthCheck() {
  const response = await fetch(`${API_BASE}/health`);
  return await response.json();
}

// 完成
