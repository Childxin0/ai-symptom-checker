/**
 * 追问面板 - ADA Health 核心功能
 * 支持选项式和文本式追问
 */
import React, { useState } from 'react';

export default function FollowupPanel({ questions, onAnswer, loading, round, maxRounds }) {
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [textAnswer, setTextAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!questions || questions.length === 0) {
    return null;
  }

  const handleSelectQuestion = (index) => {
    setSelectedQuestion(index);
    setTextAnswer('');
  };

  const handleOptionClick = async (questionIndex, option) => {
    if (submitting || loading) return;
    
    setSubmitting(true);
    try {
      await onAnswer(questionIndex, option);
    } finally {
      setSubmitting(false);
    }
  };

  const handleTextSubmit = async (questionIndex) => {
    if (!textAnswer.trim() || submitting || loading) return;
    
    setSubmitting(true);
    try {
      await onAnswer(questionIndex, textAnswer);
      setTextAnswer('');
    } finally {
      setSubmitting(false);
    }
  };

  const currentQuestion = selectedQuestion !== null ? questions[selectedQuestion] : questions[0];
  const currentIndex = selectedQuestion !== null ? selectedQuestion : 0;

  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl border-2 border-purple-200 p-6 shadow-lg animate-fadeIn">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <div>
            <h3 className="font-bold text-purple-900">需要更多信息</h3>
            <p className="text-sm text-purple-700">
              第 {round + 1}/{maxRounds} 轮追问
            </p>
          </div>
        </div>
        
        <div className="px-3 py-1 bg-purple-600 text-white text-xs font-bold rounded-full">
          {questions.length} 个问题
        </div>
      </div>

      {/* 问题选择 */}
      {questions.length > 1 && (
        <div className="flex gap-2 mb-4">
          {questions.map((_, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectQuestion(idx)}
              className={`flex-1 py-2 px-3 rounded-lg font-medium text-sm transition ${
                (selectedQuestion === idx || (selectedQuestion === null && idx === 0))
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-purple-700 border border-purple-200 hover:bg-purple-100'
              }`}
              disabled={submitting || loading}
            >
              问题 {idx + 1}
            </button>
          ))}
        </div>
      )}

      {/* 问题内容 */}
      <div className="bg-white rounded-xl p-5 shadow-sm mb-4">
        <div className="flex items-start gap-3">
          <svg className="w-6 h-6 text-purple-600 mt-1 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-lg font-medium text-gray-900 flex-1">
            {currentQuestion.question}
          </p>
        </div>
      </div>

      {/* 回答方式 */}
      {currentQuestion.options && currentQuestion.options.length > 0 ? (
        // 选项式回答
        <div className="space-y-2">
          {currentQuestion.options.map((option, idx) => (
            <button
              key={idx}
              onClick={() => handleOptionClick(currentIndex, option)}
              disabled={submitting || loading}
              className="w-full px-5 py-4 bg-white hover:bg-purple-50 border-2 border-purple-200 hover:border-purple-400 rounded-xl text-left font-medium text-gray-900 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {option}
            </button>
          ))}
        </div>
      ) : (
        // 文本式回答
        <div className="bg-white rounded-xl p-4">
          <textarea
            value={textAnswer}
            onChange={(e) => setTextAnswer(e.target.value)}
            placeholder="请输入您的回答..."
            rows={3}
            disabled={submitting || loading}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition disabled:bg-gray-50"
          />
          <button
            onClick={() => handleTextSubmit(currentIndex)}
            disabled={!textAnswer.trim() || submitting || loading}
            className="mt-3 w-full px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition font-semibold"
          >
            {submitting ? '提交中...' : '提交回答'}
          </button>
        </div>
      )}

      {/* 提示 */}
      <p className="text-xs text-purple-700 mt-4 text-center">
        根据您的回答，系统将重新评估风险等级
      </p>
    </div>
  );
}

// 完成
