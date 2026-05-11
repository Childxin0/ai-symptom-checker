/**
 * 风险等级卡片 - 对标 ADA Health
 * 支持：HIGH脉冲动画、颜色区分、加载骨架屏
 */
import React from 'react';

const RISK_STYLES = {
  EMERGENCY: {
    bg: 'bg-red-100',
    border: 'border-red-600',
    text: 'text-red-950',
    badge: 'bg-red-600',
    icon: 'text-red-700',
    label: '⚠️ 紧急',
    subtitle: '立即拨打120或前往急诊',
    pulse: true
  },
  HIGH: {
    bg: 'bg-red-50',
    border: 'border-red-500',
    text: 'text-red-900',
    badge: 'bg-red-500',
    icon: 'text-red-600',
    label: '高风险',
    subtitle: '建议尽快就医',
    pulse: true
  },
  MEDIUM: {
    bg: 'bg-orange-50',
    border: 'border-orange-500',
    text: 'text-orange-900',
    badge: 'bg-orange-500',
    icon: 'text-orange-600',
    label: '中风险',
    subtitle: '建议24-48小时内就诊',
    pulse: false
  },
  LOW: {
    bg: 'bg-green-50',
    border: 'border-green-500',
    text: 'text-green-900',
    badge: 'bg-green-500',
    icon: 'text-green-600',
    label: '低风险',
    subtitle: '可观察，注意症状变化',
    pulse: false
  }
};

export default function RiskCard({ result, loading }) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl border-2 border-gray-200 p-8 shadow-sm">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-24 mb-4"></div>
          <div className="h-10 bg-gray-200 rounded w-32 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-40 mb-6"></div>
          <div className="h-2 bg-gray-200 rounded w-full"></div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-white rounded-2xl border-2 border-dashed border-gray-300 p-8 shadow-sm">
        <div className="text-center text-gray-400">
          <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="font-medium">等待分析</p>
          <p className="text-sm mt-1">提交症状描述后显示风险评估</p>
        </div>
      </div>
    );
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 关键修复：只在 valid_symptom 时显示风险卡
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  if (result.input_type !== 'valid_symptom') {
    // 非医疗输入 或 信息不足：不显示风险卡
    return null;
  }

  // 检查是否有有效的风险数据
  if (!result.risk || !result.risk.level) {
    return null;
  }

  const riskLevel = result.risk.level;
  const style = RISK_STYLES[riskLevel] || RISK_STYLES.LOW;
  const score = result.risk.score || 0;

  return (
    <div className={`${style.bg} rounded-2xl border-2 ${style.border} p-8 shadow-lg ${style.pulse ? 'animate-danger-pulse' : ''} animate-fadeIn`}>
      {/* 标签 */}
      <div className="flex items-center gap-2 mb-3">
        <span className={`px-3 py-1 ${style.badge} text-white text-xs font-bold rounded-full uppercase tracking-wide`}>
          初筛结果
        </span>
        {result.llm_used === false && (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded">
            降级模式
          </span>
        )}
      </div>

      {/* 风险等级 */}
      <div className="flex items-center gap-4 mb-4">
        <div className={`w-16 h-16 rounded-2xl ${style.bg} ${style.border} border-2 flex items-center justify-center`}>
          {riskLevel === 'EMERGENCY' && (
            <svg className={`w-8 h-8 ${style.icon}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          )}
          {riskLevel === 'HIGH' && (
            <svg className={`w-8 h-8 ${style.icon}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          )}
          {riskLevel === 'MEDIUM' && (
            <svg className={`w-8 h-8 ${style.icon}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
          {riskLevel === 'LOW' && (
            <svg className={`w-8 h-8 ${style.icon}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
        </div>

        <div className="flex-1">
          <h2 className={`text-4xl font-bold ${style.text}`}>{style.label}</h2>
          <p className={`text-lg ${style.text} opacity-80 mt-1`}>{style.subtitle}</p>
        </div>
      </div>

      {/* 风险分数条 */}
      <div className="bg-white bg-opacity-60 rounded-lg p-3">
        <div className="flex justify-between text-sm mb-2">
          <span className={`font-medium ${style.text}`}>风险指数</span>
          <span className={`font-bold ${style.text}`}>{score}/100</span>
        </div>
        <div className="w-full bg-white rounded-full h-3 overflow-hidden">
          <div 
            className={`h-full ${style.badge} transition-all duration-1000 ease-out`}
            style={{ width: `${score}%` }}
          ></div>
        </div>
      </div>

      {/* 时间线 */}
      {result.urgency_timeline && (
        <div className={`mt-4 px-4 py-3 bg-white bg-opacity-60 rounded-lg`}>
          <div className="flex items-center gap-2">
            <svg className={`w-5 h-5 ${style.icon}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className={`text-sm font-semibold ${style.text}`}>
              {result.urgency_timeline}
            </span>
          </div>
        </div>
      )}

      {/* 处理时间 */}
      {result.processing_time_ms > 0 && (
        <p className="text-xs text-gray-500 mt-4 text-center">
          分析耗时: {result.processing_time_ms}ms
        </p>
      )}
    </div>
  );
}

// 完成
