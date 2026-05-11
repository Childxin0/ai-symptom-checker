/**
 * 演示模式 - 右下角悬浮按钮 + 预设案例选择面板
 */
import React, { useState } from 'react';

const DEMO_CASES = [
  {
    id: 1,
    level: 'EMERGENCY',
    title: '急症：外伤大出血',
    desc: '外伤急症 · 立即拨打 120',
    text: '被车撞了，头部受伤，一直在大量出血，止不住',
    color: {
      badge: 'bg-red-100 text-red-700 border-red-200',
      border: 'border-red-200 hover:border-red-400',
      icon: 'text-red-500',
      bg: 'hover:bg-red-50',
    },
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
  },
  {
    id: 2,
    level: 'MEDIUM',
    title: '中危：发热伴腹痛',
    desc: '发热感染 · 建议尽快就诊',
    text: '发烧两天了，体温38.2度，伴随腹痛，吃了退烧药没太大用',
    color: {
      badge: 'bg-orange-100 text-orange-700 border-orange-200',
      border: 'border-orange-200 hover:border-orange-400',
      icon: 'text-orange-500',
      bg: 'hover:bg-orange-50',
    },
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    id: 3,
    level: 'LOW',
    title: '低危：轻度头痛疲劳',
    desc: '生活作息 · 可自我观察',
    text: '最近轻微头痛，睡眠质量差，白天有点疲劳，没有其他症状',
    color: {
      badge: 'bg-green-100 text-green-700 border-green-200',
      border: 'border-green-200 hover:border-green-400',
      icon: 'text-green-500',
      bg: 'hover:bg-green-50',
    },
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
];

export default function DemoMode({ onSelectCase }) {
  const [open, setOpen] = useState(false);

  const handleSelect = (caseText) => {
    setOpen(false);
    onSelectCase(caseText);
  };

  return (
    <>
      {/* 遮罩层 */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
          onClick={() => setOpen(false)}
        />
      )}

      {/* 选择面板 */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-80 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden animate-fadeIn">
          {/* 面板标题 */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-gray-50">
            <div>
              <p className="font-bold text-gray-900 text-sm">演示案例</p>
              <p className="text-xs text-gray-500 mt-0.5">点击任一案例自动填入并分析</p>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="w-7 h-7 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-200 transition"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* 案例列表 */}
          <div className="p-3 space-y-2">
            {DEMO_CASES.map((c) => (
              <button
                key={c.id}
                onClick={() => handleSelect(c.text)}
                className={`w-full text-left p-4 rounded-xl border-2 transition-all ${c.color.border} ${c.color.bg} group`}
              >
                <div className="flex items-start gap-3">
                  <span className={`mt-0.5 flex-shrink-0 ${c.color.icon}`}>{c.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-gray-900 text-sm">{c.title}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${c.color.badge}`}>
                        {c.level}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mb-2">{c.desc}</p>
                    <p className="text-xs text-gray-700 leading-relaxed line-clamp-2 italic">
                      "{c.text}"
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>

          <div className="px-5 py-3 border-t border-gray-100 bg-gray-50">
            <p className="text-xs text-gray-400 text-center">仅供演示，不构成医疗建议</p>
          </div>
        </div>
      )}

      {/* 悬浮按钮 */}
      <button
        onClick={() => setOpen(prev => !prev)}
        className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 px-5 py-3 rounded-full shadow-lg font-semibold text-sm transition-all
          ${open
            ? 'bg-gray-700 text-white shadow-xl scale-95'
            : 'bg-blue-600 hover:bg-blue-700 text-white hover:shadow-xl hover:scale-105'
          }`}
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        演示模式
      </button>
    </>
  );
}
