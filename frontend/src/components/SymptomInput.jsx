/**
 * 症状输入区 - 对标 ADA Health
 * 支持：字数统计、示例填充、历史记录
 */
import React, { useState, useEffect } from 'react';
import demoCases from '../data/demo_cases.json';

const MAX_CHARS = 2000;

export default function SymptomInput({ value, onChange, onAnalyze, loading, disabled }) {
  const [charCount, setCharCount] = useState(0);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    setCharCount(value.length);
    // 从 localStorage 加载历史记录
    try {
      const saved = localStorage.getItem('symptom_history');
      if (saved) {
        setHistory(JSON.parse(saved));
      }
    } catch (e) {
      console.error('加载历史失败:', e);
    }
  }, [value]);

  const handleChange = (e) => {
    const newValue = e.target.value;
    if (newValue.length <= MAX_CHARS) {
      onChange(newValue);
    }
  };

  const handleAnalyze = () => {
    if (value.trim()) {
      // 保存到历史
      const newHistory = [value, ...history.filter(h => h !== value)].slice(0, 3);
      setHistory(newHistory);
      try {
        localStorage.setItem('symptom_history', JSON.stringify(newHistory));
      } catch (e) {
        console.error('保存历史失败:', e);
      }
      
      onAnalyze();
    }
  };

  const fillExample = () => {
    const randomCase = demoCases[Math.floor(Math.random() * demoCases.length)];
    onChange(randomCase.text);
  };

  const fillFromHistory = (text) => {
    onChange(text);
  };

  const charCountClass = charCount > MAX_CHARS * 0.9 
    ? 'char-counter danger' 
    : charCount > MAX_CHARS * 0.7 
    ? 'char-counter warning' 
    : 'char-counter';

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      <h2 className="text-xl font-bold text-gray-900 mb-2">描述您的症状</h2>
      <p className="text-sm text-gray-600 mb-4">
        请尽量详细描述您的不适，包括部位、程度、持续时间和伴随症状
      </p>

      {/* 输入框 */}
      <div className="relative">
        <textarea
          value={value}
          onChange={handleChange}
          disabled={loading || disabled}
          placeholder="例如：我头疼三天了，昨晚发烧38.5度，有点恶心，吃不下东西..."
          className="w-full h-48 p-4 border border-gray-300 rounded-xl resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition disabled:bg-gray-50 disabled:cursor-not-allowed text-gray-900"
          style={{ fontSize: '15px', lineHeight: '1.6' }}
        />
        
        {/* 字数统计 */}
        <div className={`absolute bottom-3 right-3 ${charCountClass}`}>
          {charCount} / {MAX_CHARS}
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex flex-wrap gap-3 mt-4">
        <button
          onClick={handleAnalyze}
          disabled={!value.trim() || loading || disabled}
          className="flex-1 min-w-[200px] px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition font-semibold flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>分析中...</span>
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <span>分析症状</span>
            </>
          )}
        </button>

        <button
          onClick={fillExample}
          disabled={loading || disabled}
          className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:border-blue-500 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
        >
          填入示例
        </button>
      </div>

      {/* 历史记录 */}
      {history.length > 0 && !loading && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs font-semibold text-gray-500 uppercase mb-2">最近输入</p>
          <div className="space-y-2">
            {history.map((item, index) => (
              <button
                key={index}
                onClick={() => fillFromHistory(item)}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-lg transition truncate"
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// 完成
