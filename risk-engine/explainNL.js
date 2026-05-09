/**
 * 面向终端用户的自然语言解释（不包含规则引擎/关键词等内部术语）。
 */

function joinSymptoms(symptoms) {
  const list = (symptoms || []).filter(Boolean).slice(0, 8);
  if (!list.length) return "";
  return `您提到的「${list.join("」「")}」`;
}

function localizeSignal(k) {
  const t = String(k);
  if (/suicid/i.test(t)) return "自杀或自伤相关表述";
  if (/chest\s*pain/i.test(t)) return "胸部不适或疼痛";
  if (/shortness\s*of\s*breath/i.test(t)) return "呼吸费力或气促";
  if (/loss\s*of\s*consciousness/i.test(t)) return "意识障碍相关表述";
  return t;
}

function pickUserFacing(list, limit = 5) {
  const u = [...new Set(list || [])].map(localizeSignal);
  const zh = u.filter((s) => /[\u4e00-\u9fff]/.test(String(s)));
  const picked = (zh.length ? zh : u).slice(0, limit);
  return picked.filter(Boolean);
}

function formatSignals(ruleEvaluation) {
  const high = pickUserFacing(ruleEvaluation.matched_keywords?.HIGH || []);
  const med = pickUserFacing(ruleEvaluation.matched_keywords?.MEDIUM || []);
  return { high, med };
}

/**
 * @param {object} opts
 * @param {'LOW'|'MEDIUM'|'HIGH'} opts.finalRisk
 * @param {object} opts.ruleEvaluation - evaluateRules 结果（内部使用，不外泄字段名）
 * @param {string[]} [opts.symptoms]
 */
export function buildNaturalExplainability({
  finalRisk,
  ruleEvaluation,
  symptoms = [],
}) {
  const { high, med } = formatSignals(ruleEvaluation);
  const symptomLead = joinSymptoms(symptoms);

  if (finalRisk === "HIGH") {
    const clue =
      high.length > 0
        ? `您的描述中包含可能需要优先排除的危险信号（例如：${high.join("、")}）。`
        : symptomLead
          ? `${symptomLead}与当前信息结合起来看，存在急症风险的可能。`
          : "综合您的描述，存在需要优先处理的急症风险信号。";
    return `${clue}因此本次初步评估为高风险。建议您立即前往急诊或拨打急救电话，不要独自忍耐或延误。`;
  }

  if (finalRisk === "MEDIUM") {
    const clue =
      med.length > 0
        ? `我们注意到您的不适可能与「${med.join("」「")}」等相关表现有关。`
        : symptomLead
          ? `${symptomLead}，需要进一步评估以排除潜在器质性或急性加重因素。`
          : "根据您目前的描述，症状强度或持续时间尚不足以自行判断轻重。";
    return `${clue}因此初步评估为中风险。建议您在短期内安排线下就诊或通过互联网医院进行复诊；若症状加重，请及时急诊。`;
  }

  const clue = symptomLead
    ? `${symptomLead}，目前尚不足以提示急危情况，但仍需留意变化。`
    : "结合现有信息，暂未识别出典型的高危急症线索。";
  return `${clue}初步评估为低风险。若症状新发、持续加重或影响日常生活，仍建议预约门诊进一步评估。`;
}
