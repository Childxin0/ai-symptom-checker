import { RISK_KEYWORDS, DEPARTMENT_HINTS } from "./keywords.js";

const ORDER = { LOW: 0, MEDIUM: 1, HIGH: 2 };

function maxRisk(a, b) {
  return ORDER[a] >= ORDER[b] ? a : b;
}

/**
 * 在原文与症状列表中匹配关键词，得到规则层风险与解释依据。
 */
export function evaluateRules(userText, symptoms = []) {
  const text = `${userText || ""} ${(symptoms || []).join(" ")}`.toLowerCase();

  const matched = { HIGH: [], MEDIUM: [], LOW: [] };

  for (const level of ["HIGH", "MEDIUM", "LOW"]) {
    for (const kw of RISK_KEYWORDS[level]) {
      const k = kw.toLowerCase();
      if (text.includes(k)) {
        matched[level].push(kw);
      }
    }
  }

  let risk = "LOW";
  if (matched.HIGH.length) risk = "HIGH";
  else if (matched.MEDIUM.length) risk = "MEDIUM";
  else if (matched.LOW.length) risk = "LOW";

  const reasons = [];
  if (matched.HIGH.length) {
    reasons.push(`命中高风险关键词：${[...new Set(matched.HIGH)].slice(0, 5).join("、")}`);
  }
  if (matched.MEDIUM.length && risk !== "HIGH") {
    reasons.push(`命中中风险关键词：${[...new Set(matched.MEDIUM)].slice(0, 5).join("、")}`);
  }

  return {
    risk_level: risk,
    matched_keywords: matched,
    rule_reasons: reasons,
  };
}

export function suggestDepartment(userText, symptoms = []) {
  const blob = `${userText || ""} ${(symptoms || []).join(" ")}`;
  for (const hint of DEPARTMENT_HINTS) {
    if (hint.keys.some((k) => blob.includes(k))) {
      return hint.department;
    }
  }
  return "全科 / 预检分诊（建议线下评估）";
}

/**
 * 合并 AI 风险与规则风险：取较高等级（安全优先）。
 */
export function mergeRiskLevels(aiRisk, ruleRisk) {
  return maxRisk(
    ORDER[aiRisk] !== undefined ? aiRisk : "LOW",
    ORDER[ruleRisk] !== undefined ? ruleRisk : "LOW"
  );
}

export function buildExplainability({
  finalRisk,
  ruleEvaluation,
  aiExplanation,
  mergedFromRules,
}) {
  const parts = [];

  if (finalRisk === "HIGH") {
    if (ruleEvaluation.rule_reasons.length) {
      parts.push("综合判定为 HIGH：规则引擎命中急危相关关键词。");
      parts.push(ruleEvaluation.rule_reasons.join("；"));
    } else {
      parts.push("综合判定为 HIGH：模型结合全文语境给出急症风险提示（已由规则上限兜底）。");
    }
    if (mergedFromRules && aiExplanation) {
      parts.push(`模型辅助说明：${aiExplanation}`);
    } else if (aiExplanation && !mergedFromRules) {
      parts.push(`模型说明：${aiExplanation}`);
    }
  } else if (finalRisk === "MEDIUM") {
    parts.push("判定为 MEDIUM：症状具有一定严重性或使用药物/诱因不确定。");
    if (ruleEvaluation.rule_reasons.length) {
      parts.push(ruleEvaluation.rule_reasons.join("；"));
    }
    if (aiExplanation) parts.push(`补充说明：${aiExplanation}`);
  } else {
    parts.push("判定为 LOW：未命中规则引擎中的中高危关键词，仍建议关注变化。");
    if (aiExplanation) parts.push(`说明：${aiExplanation}`);
  }

  return parts.join(" ");
}
