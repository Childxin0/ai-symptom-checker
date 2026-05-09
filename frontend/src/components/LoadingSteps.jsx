/**
 * 加载步骤指示器 - 增强用户体验
 */
import React, { useState, useEffect } from 'react';

const STEPS = [
  { label: '正在识别症状...', icon: '🔍', duration: 2000 },
  { label: '风险评估中...', icon: '⚕️', duration: 1500 },
  { label: '生成建议...', icon: '📋', duration: 1000 },
];

export default function LoadingSteps() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (currentStep < STEPS.length - 1) {
      const timer = setTimeout(() => {
        setCurrentStep(prev => prev + 1);
      }, STEPS[currentStep].duration);
      return () => clearTimeout(timer);
    }
  }, [currentStep]);

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm">
      <div className="flex flex-col items-center">
        {/* 动画图标 */}
        <div className="w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center mb-6 animate-pulse">
          <svg className="w-12 h-12 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>

        {/* 步骤列表 */}
        <div className="w-full space-y-3">
          {STEPS.map((step, idx) => (
            <div 
              key={idx}
              className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                idx === currentStep 
                  ? 'bg-blue-50 border border-blue-200' 
                  : idx < currentStep 
                  ? 'bg-green-50 border border-green-200' 
                  : 'bg-gray-50 border border-gray-200'
              }`}
            >
              <span className="text-2xl">{step.icon}</span>
              <span className={`font-medium ${
                idx === currentStep 
                  ? 'text-blue-900' 
                  : idx < currentStep 
                  ? 'text-green-900' 
                  : 'text-gray-500'
              }`}>
                {step.label}
              </span>
              {idx < currentStep && (
                <svg className="w-5 h-5 text-green-600 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// 完成
