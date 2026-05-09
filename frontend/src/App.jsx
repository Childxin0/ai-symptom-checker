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
import { analyzeSymptoms, answerFollowup } from './api';

const DEMO_TEXT = "我头疼三天了，昨晚发烧38.5度，有点恶心，吃不下东西";

export default function App() {
  const [userInput, setUserInput] = useState(DEMO_TEXT);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

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

  const handleAnswerFollowup = async (questionIndex, answer) => {
    if (!result?.session_id) return;

    setLoading(true);
    setError(null);

    try {
      const data = await answerFollowup(result.session_id, answer, questionIndex);
      setResult(data);
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
            {/* 风险卡片 */}
            {loading ? (
              <LoadingSteps />
            ) : (
              <RiskCard result={result} loading={false} />
            )}

            {/* 追问面板 */}
            {result?.needs_followup && !loading && (
              <FollowupPanel
                questions={result.followup_questions}
                onAnswer={handleAnswerFollowup}
                loading={loading}
                round={result.followup_round}
                maxRounds={3}
              />
            )}

            {/* 结果面板 */}
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
    </div>
  );
}

// 完成
