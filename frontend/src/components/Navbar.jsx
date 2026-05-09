/**
 * 顶部导航栏 - 商业级标准
 */
import React, { useState } from 'react';

export default function Navbar() {
  const [showDisclaimer, setShowDisclaimer] = useState(false);

  return (
    <>
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo 和标题 */}
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">AI 症状初筛</h1>
                <p className="text-xs text-gray-500">Symptom Analysis System</p>
              </div>
            </div>

            {/* 右侧按钮 */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowDisclaimer(true)}
                className="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded-lg hover:bg-gray-100 transition"
              >
                免责声明
              </button>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.220-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.137 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z" clipRule="evenodd" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* 免责声明弹窗 */}
      {showDisclaimer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-8 shadow-2xl animate-fadeIn">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">免责声明</h2>
            <div className="prose text-gray-600 space-y-4">
              <p>
                本系统为 <strong>AI 产品演示</strong>，仅用于展示人工智能在医疗初筛场景的应用可能性。
              </p>
              <p className="font-semibold text-red-600">
                重要提示：
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li>本系统不能替代专业医疗诊断</li>
                <li>不构成任何医疗建议或治疗方案</li>
                <li>分析结果仅供参考，不作为就医依据</li>
                <li>如有严重或紧急症状，请立即拨打 120 或前往急诊</li>
              </ul>
              <p className="text-sm">
                本项目使用 Anthropic Claude API 进行症状分析，结合规则引擎进行风险分层。
                所有数据仅用于演示，不会被存储或用于其他用途。
              </p>
            </div>
            <div className="mt-8 flex justify-end">
              <button
                onClick={() => setShowDisclaimer(false)}
                className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
              >
                我已知晓
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// 完成
