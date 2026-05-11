/**
 * 追问面板 - 多题统一收集，一次性提交
 *
 * 状态设计：
 *   answers: { [qIndex]: { quickOption: string|null, textInput: string } }
 *   切换 tab 时 answers 不清空，保留所有已填内容
 *   底部统一一个"提交所有回答"按钮
 */
import React, { useState } from 'react';

// ── 每种 question_type 对应的快捷按钮选项 ────────────────────────────
const QUICK_OPTIONS_MAP = {
  yn:       ['是', '否', '不确定'],
  duration: ['几小时内', '1-2天', '3天以上', '超过一周'],
  severity: ['轻微', '中等', '严重'],
  location: ['头部', '胸部', '腹部', '四肢', '其他'],
  open:     [],
};

// 提交时用于拼接自然语言的标签
const TYPE_LABEL = {
  yn:       '伴随症状',
  duration: '持续时间',
  severity: '严重程度',
  location: '不适部位',
  open:     '补充描述',
};

// 按问题类型分配颜色主题
const TYPE_COLOR = {
  yn:       'purple',
  duration: 'blue',
  severity: 'orange',
  location: 'teal',
  open:     'purple',
};

const CLS = {
  purple: {
    btn_sel:    'bg-purple-600 text-white border-purple-600 shadow-md',
    btn_idle:   'bg-white text-purple-700 border-purple-200 hover:border-purple-400 hover:bg-purple-50',
    badge:      'bg-purple-100 text-purple-700 border-purple-200',
    ring:       'focus:ring-purple-400 focus:border-purple-400',
    tab_active: 'bg-purple-600 text-white border-purple-600',
    tab_idle:   'bg-white text-purple-700 border-purple-200 hover:bg-purple-50',
    tab_done:   'bg-purple-100 text-purple-800 border-purple-300',
  },
  blue: {
    btn_sel:    'bg-blue-600 text-white border-blue-600 shadow-md',
    btn_idle:   'bg-white text-blue-700 border-blue-200 hover:border-blue-400 hover:bg-blue-50',
    badge:      'bg-blue-100 text-blue-700 border-blue-200',
    ring:       'focus:ring-blue-400 focus:border-blue-400',
    tab_active: 'bg-blue-600 text-white border-blue-600',
    tab_idle:   'bg-white text-blue-700 border-blue-200 hover:bg-blue-50',
    tab_done:   'bg-blue-100 text-blue-800 border-blue-300',
  },
  orange: {
    btn_sel:    'bg-orange-500 text-white border-orange-500 shadow-md',
    btn_idle:   'bg-white text-orange-700 border-orange-200 hover:border-orange-400 hover:bg-orange-50',
    badge:      'bg-orange-100 text-orange-700 border-orange-200',
    ring:       'focus:ring-orange-400 focus:border-orange-400',
    tab_active: 'bg-orange-500 text-white border-orange-500',
    tab_idle:   'bg-white text-orange-700 border-orange-200 hover:bg-orange-50',
    tab_done:   'bg-orange-100 text-orange-800 border-orange-300',
  },
  teal: {
    btn_sel:    'bg-teal-600 text-white border-teal-600 shadow-md',
    btn_idle:   'bg-white text-teal-700 border-teal-200 hover:border-teal-400 hover:bg-teal-50',
    badge:      'bg-teal-100 text-teal-700 border-teal-200',
    ring:       'focus:ring-teal-400 focus:border-teal-400',
    tab_active: 'bg-teal-600 text-white border-teal-600',
    tab_idle:   'bg-white text-teal-700 border-teal-200 hover:bg-teal-50',
    tab_done:   'bg-teal-100 text-teal-800 border-teal-300',
  },
};

/** 判断某题是否已回答 */
const isAnswered = (ans) =>
  ans && (ans.quickOption || (ans.textInput && ans.textInput.trim()));

/** 将 answers 对象序列化为自然语言摘要，用于合并到原始输入 */
const buildSummary = (questions, answers) => {
  const parts = questions.map((q, idx) => {
    const ans = answers[idx];
    if (!isAnswered(ans)) return null;
    const label = TYPE_LABEL[q.question_type] || q.question;
    const value = [
      ans.quickOption,
      ans.textInput?.trim() ? `（${ans.textInput.trim()}）` : '',
    ]
      .filter(Boolean)
      .join('');
    return `${label}：${value}`;
  });
  return parts.filter(Boolean).join('；');
};

// ── 主组件 ────────────────────────────────────────────────────────────
export default function FollowupPanel({
  questions,
  onAnswer,
  loading,
  round = 0,
  maxRounds = 3,
}) {
  // { [qIndex]: { quickOption: string|null, textInput: string } }
  const [answers, setAnswers] = useState({});
  const [activeTab, setActiveTab] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  if (!questions || questions.length === 0) return null;

  const currentQ = questions[activeTab] ?? questions[0];
  const qType    = currentQ.question_type || 'yn';
  const color    = TYPE_COLOR[qType] || 'purple';
  const cls      = CLS[color];
  const options  = QUICK_OPTIONS_MAP[qType] ?? [];

  const curAns   = answers[activeTab] ?? { quickOption: null, textInput: '' };
  const answeredCount = questions.filter((_, i) => isAnswered(answers[i])).length;
  const canSubmit = !submitting && !loading && answeredCount >= 1;

  // ── 更新某题的部分字段 ────────────────────────────────────────────
  const patch = (idx, partial) =>
    setAnswers(prev => ({
      ...prev,
      [idx]: { quickOption: null, textInput: '', ...prev[idx], ...partial },
    }));

  const toggleQuick = (opt) => {
    const next = curAns.quickOption === opt ? null : opt;
    patch(activeTab, { quickOption: next });
  };

  // ── 统一提交：序列化所有回答 ──────────────────────────────────────
  const handleSubmitAll = async () => {
    if (!canSubmit) return;
    const summary = buildSummary(questions, answers);
    setSubmitting(true);
    try {
      // App.jsx 的 handleAnswerFollowup(questionText, answer, supplement)
      // 会拼接成：补充：追问补充信息 → <summary>
      await onAnswer('追问补充信息', summary, '');
      setAnswers({});       // 提交成功后清空，等待下一轮
      setActiveTab(0);
    } finally {
      setSubmitting(false);
    }
  };

  // ── 渲染 ──────────────────────────────────────────────────────────
  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl border-2 border-purple-200 p-6 shadow-lg animate-fadeIn">

      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <div>
            <h3 className="font-bold text-purple-900 text-base">需要更多信息</h3>
            <p className="text-xs text-purple-600 mt-0.5">
              第 <span className="font-semibold">{round + 1}</span> 轮追问，共最多{' '}
              <span className="font-semibold">{maxRounds}</span> 轮
            </p>
          </div>
        </div>
        <span className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded-full border border-purple-200">
          已填 {answeredCount}/{questions.length}
        </span>
      </div>

      {/* Tab 切换（多个问题时显示）*/}
      {questions.length > 1 && (
        <div className="flex gap-2 mb-4">
          {questions.map((q, idx) => {
            const tType  = q.question_type || 'yn';
            const tColor = TYPE_COLOR[tType] || 'purple';
            const tCls   = CLS[tColor];
            const done   = isAnswered(answers[idx]);
            const active = activeTab === idx;

            return (
              <button
                key={idx}
                onClick={() => setActiveTab(idx)}
                disabled={submitting || loading}
                className={`flex-1 py-2 px-2 rounded-lg text-xs font-medium transition-all border
                  ${active ? tCls.tab_active
                    : done   ? tCls.tab_done
                    : tCls.tab_idle}
                  disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {done && !active && (
                  <span className="mr-1">✓</span>
                )}
                {TYPE_LABEL[tType] || `问题 ${idx + 1}`}
              </button>
            );
          })}
        </div>
      )}

      {/* 当前问题文本 */}
      <div className="bg-white rounded-xl p-4 shadow-sm mb-5 flex items-start gap-3">
        <svg className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div className="flex-1">
          <p className="text-gray-900 font-medium leading-relaxed">{currentQ.question}</p>
          {qType !== 'open' && (
            <span className={`inline-block mt-2 text-xs px-2 py-0.5 rounded-full border font-medium ${cls.badge}`}>
              {TYPE_LABEL[qType]}
            </span>
          )}
        </div>
      </div>

      {/* 快捷按钮区（open 类型不显示）*/}
      {options.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-purple-700 font-medium mb-2">快捷回答</p>
          <div className={`grid gap-2 ${options.length <= 3 ? 'grid-cols-3' : 'grid-cols-2'}`}>
            {options.map(opt => (
              <button
                key={opt}
                onClick={() => toggleQuick(opt)}
                disabled={submitting || loading}
                className={`py-2.5 rounded-xl font-semibold text-sm transition-all border-2
                  ${curAns.quickOption === opt ? cls.btn_sel : cls.btn_idle}
                  disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 补充文本框 */}
      <div className="mb-5">
        <p className="text-xs text-purple-700 font-medium mb-2">
          {qType === 'open' ? '请详细描述' : '补充描述'}
          {qType !== 'open' && (
            <span className="text-purple-400 font-normal ml-1">（选填）</span>
          )}
        </p>
        <textarea
          value={curAns.textInput}
          onChange={(e) => patch(activeTab, { textInput: e.target.value })}
          placeholder={
            qType === 'open'
              ? '请在此详细说明…'
              : '可补充更多细节，例如：夜间更严重…'
          }
          rows={qType === 'open' ? 3 : 2}
          disabled={submitting || loading}
          className={`w-full px-4 py-3 bg-white border-2 border-purple-100 rounded-xl resize-none text-sm
            focus:ring-2 ${cls.ring} transition
            disabled:bg-gray-50 placeholder-gray-400`}
        />
      </div>

      {/* 统一提交按钮 */}
      <button
        onClick={handleSubmitAll}
        disabled={!canSubmit}
        className={`w-full py-3.5 font-semibold rounded-xl transition-all shadow-sm
          hover:shadow-md text-white
          ${canSubmit
            ? 'bg-purple-600 hover:bg-purple-700'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'}`}
      >
        {submitting ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            分析中…
          </span>
        ) : (
          `提交回答（已填 ${answeredCount}/${questions.length} 题）`
        )}
      </button>

      {answeredCount === 0 && (
        <p className="text-xs text-purple-400 mt-2 text-center">
          至少填写 1 题即可提交
        </p>
      )}

      <p className="text-xs text-purple-500 mt-2 text-center">
        系统将结合原始描述和所有追问回答重新评估风险
      </p>
    </div>
  );
}
