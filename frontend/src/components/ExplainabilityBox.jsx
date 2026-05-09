/**
 * 可折叠的解释说明区域（浅灰背景区分）。
 */

import { useState } from "react";

export default function ExplainabilityBox({ text, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);

  if (!text) return null;

  return (
    <div className="overflow-hidden rounded-xl border border-clinical-200 bg-clinical-100/80">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-clinical-800 hover:bg-clinical-100"
        aria-expanded={open}
      >
        <span>为何是这个风险等级？</span>
        <span className="text-clinical-400">{open ? "收起" : "展开"}</span>
      </button>
      {open && (
        <div className="border-t border-clinical-200 px-4 py-3 text-sm leading-relaxed text-clinical-700">
          {text.split("\n").map((line, i) => (
            <p key={i} className={i > 0 ? "mt-2" : ""}>
              {line}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
