/**
 * 结果展示面板 - 商业级多卡片布局
 * 包含：症状识别、就诊建议、科室推荐、可解释性
 */
import React, { useState } from 'react';

export default function ResultPanel({ result, loading }) {
  const [explainOpen, setExplainOpen] = useState(false);

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-32 mb-4"></div>
            <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-white rounded-xl border border-dashed border-gray-300 p-8 text-center text-gray-400">
        <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="font-medium">等待结果</p>
        <p className="text-sm mt-1">分析完成后这里将显示详细信息</p>
      </div>
    );
  }

  const symptoms = result.structured?.symptoms || [];
  const hasSymptoms = symptoms.length > 0 && symptoms[0] !== '待详细分析';

  return (
    <div className="space-y-4 animate-fadeIn">
      {/* 症状识别 */}
      {hasSymptoms && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            识别的症状
          </h3>
          <div className="flex flex-wrap gap-2">
            {symptoms.map((symptom, idx) => (
              <span key={idx} className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium border border-blue-200">
                {symptom}
              </span>
            ))}
          </div>
          
          {/* 症状详情 */}
          <div className="mt-4 grid grid-cols-2 gap-3">
            {result.structured.duration && (
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">持续时间</p>
                <p className="text-sm font-semibold text-gray-900">{result.structured.duration}</p>
              </div>
            )}
            {result.structured.severity && (
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">严重程度</p>
                <p className="text-sm font-semibold text-gray-900">{result.structured.severity}</p>
              </div>
            )}
            {result.structured.temperature && (
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">体温</p>
                <p className="text-sm font-semibold text-gray-900">{result.structured.temperature}°C</p>
              </div>
            )}
            {result.structured.symptom_onset && result.structured.symptom_onset !== '不确定' && (
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">发病方式</p>
                <p className="text-sm font-semibold text-gray-900">{result.structured.symptom_onset}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 就诊建议 */}
      <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border-2 border-blue-200 p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-blue-900 uppercase mb-3 flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          就诊建议
        </h3>
        <p className="text-gray-800 leading-relaxed whitespace-pre-line">
          {result.advice}
        </p>
        
        {result.recommended_department && (
          <div className="mt-4 pt-4 border-t border-blue-200">
            <p className="text-sm text-blue-900 mb-2 font-medium">推荐科室</p>
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-lg border border-blue-200">
              <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <span className="font-semibold text-gray-900">{result.recommended_department}</span>
            </div>
          </div>
        )}
      </div>

      {/* 可解释性面板 */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <button
          onClick={() => setExplainOpen(!explainOpen)}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition"
        >
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-semibold text-gray-900">为什么是这个风险等级？</span>
          </div>
          <svg className={`w-5 h-5 text-gray-400 transition-transform ${explainOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {explainOpen && (
          <div className="px-6 pb-6 border-t border-gray-200 pt-4 animate-fadeIn">
            <p className="text-gray-700 leading-relaxed mb-4 whitespace-pre-line">
              {result.explainability}
            </p>

            {result.risk?.triggered_rules && result.risk.triggered_rules.length > 0 && (
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm font-semibold text-gray-700 mb-2">触发的规则</p>
                <div className="space-y-2">
                  {result.risk.rule_explanations?.map((exp, idx) => (
                    <div key={idx} className="flex items-start gap-2">
                      <svg className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="text-sm text-gray-700">{exp}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.rationale && (
              <div className="mt-4 bg-blue-50 rounded-lg p-4 border border-blue-100">
                <p className="text-sm font-semibold text-blue-900 mb-2">AI 分析过程</p>
                <p className="text-sm text-gray-700 leading-relaxed">
                  {result.rationale}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// 完成
