/**
 * 主应用 - 商业级布局，对标 ADA Health
 */
import React, { useState } from 'react';
import Navbar from './components/Navbar';
import SymptomInput from './components/SymptomInput';
import RiskCard from './components/RiskCard';
import ResultPanel from './components/ResultPanel';
import FollowupPanel from './components/FollowupPanel';
import LoadingSteps from './components/LoadingSteps';
import DemoMode from './components/DemoMode';
import { analyzeSymptoms } from './api';

const MAX_FOLLOWUP_ROUNDS = 3;

export default function App() {
  const [userInput, setUserInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // 多轮追问状态
  const [originalInput, setOriginalInput] = useState('');
  const [followupRound, setFollowupRound] = useState(0);
  const [followupHistory, setFollowupHistory] = useState([]); // [{q, a}]

  /** 演示模式：填入案例文本并自动触发分析 */
  const handleDemoSelect = (text) => {
    setUserInput(text);
    // 延一帧让 state 更新后再触发分析
    setTimeout(() => triggerAnalyze(text), 0);
  };

  const triggerAnalyze = async (input) => {
    const text = (input ?? userInput).trim();
    if (!text) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setFollowupRound(0);
    setFollowupHistory([]);
    setOriginalInput(text);
    try {
      const data = await analyzeSymptoms(text);
      setResult(data);
    } catch (err) {
      setError(err.message || '分析失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setFollowupRound(0);
    setFollowupHistory([]);
    setOriginalInput(userInput);

    try {
      const data = await analyzeSymptoms(userInput);
      setResult(data);
    } catch (err) {
      setError(err.message || '分析失败，请重试');
      console.error('分析错误:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 追问回答：将原始输入 + 历史QA + 本次回答合并后重新分析
   * @param {string} questionText  当前问题文本
   * @param {string} answer        快捷回答（是/否/不确定）或自由文本
   * @param {string} supplement    补充描述（可选）
   */
  const handleAnswerFollowup = async (questionText, answer, supplement = '') => {
    if (followupRound >= MAX_FOLLOWUP_ROUNDS) return;

    const newQA = { q: questionText, a: answer + (supplement ? `（${supplement}）` : '') };
    const updatedHistory = [...followupHistory, newQA];

    // 构建合并文本：原始输入 + 所有追问QA
    const historyText = updatedHistory
      .map(({ q, a }) => `补充：${q} → ${a}`)
      .join('\n');
    const combined = [originalInput, historyText].filter(Boolean).join('\n');

    setLoading(true);
    setError(null);

    try {
      const data = await analyzeSymptoms(combined, result?.session_id);
      const nextRound = followupRound + 1;
      setResult({ ...data, followup_round: nextRound });
      setFollowupRound(nextRound);
      setFollowupHistory(updatedHistory);
    } catch (err) {
      setError(err.message || '追问失败，请重试');
      console.error('追问错误:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 错误提示 */}
        {error && (
          <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-xl p-4 flex items-start gap-3 animate-fadeIn">
            <svg className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="font-semibold text-red-900">分析失败</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
            <button 
              onClick={() => setError(null)}
              className="text-red-600 hover:text-red-800"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* 主内容区 - 左右布局 */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* 左栏：输入区 */}
          <div className="space-y-6">
            <SymptomInput
              value={userInput}
              onChange={setUserInput}
              onAnalyze={handleAnalyze}
              loading={loading}
              disabled={loading}
            />
          </div>

          {/* 右栏：结果区 */}
          <div className="space-y-6">
            {/* 风险卡片 - 仅在有效症状时显示 */}
            {loading ? (
              <LoadingSteps />
            ) : (
              <RiskCard result={result} loading={false} />
            )}

            {/* 追问面板 - valid_symptom 或 insufficient_symptom 均可触发，未超轮次限制 */}
            {(result?.input_type === 'valid_symptom' || result?.input_type === 'insufficient_symptom') &&
              result?.needs_followup && followupRound < MAX_FOLLOWUP_ROUNDS && !loading && (
              <FollowupPanel
                questions={result.followup_questions}
                onAnswer={handleAnswerFollowup}
                loading={loading}
                round={followupRound}
                maxRounds={MAX_FOLLOWUP_ROUNDS}
              />
            )}

            {/* 结果面板 - 根据 input_type 显示不同内容 */}
            {!loading && (
              <ResultPanel result={result} loading={false} />
            )}
          </div>
        </div>

        {/* 页脚 */}
        <footer className="mt-16 py-8 border-t border-gray-200 text-center text-sm text-gray-500">
          <p className="mb-2">
            <strong className="text-gray-700">免责声明：</strong>
            本系统为演示用途，不构成医疗建议。急危重症请拨打 120 或前往急诊。
          </p>
          <p>
            © 2026 AI 症状初筛系统 · 商业级 MVP
          </p>
        </footer>
      </main>

      {/* 演示模式悬浮入口 */}
      <DemoMode onSelectCase={handleDemoSelect} />
    </div>
  );
}

// 完成
