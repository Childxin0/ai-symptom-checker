"""
验证两个问题的修复：
1. 否定句过滤（症状字段不含被否定的词）
2. insufficient_symptom 触发追问逻辑
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.text_preprocessor import get_negated_terms, filter_negations
from core.input_validator import validate_input
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

passed = 0
failed = 0


def check(label, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        failed += 1
        print(f"  [FAIL] {label}")
    if detail:
        print(f"         {detail}")
    return condition


# ──────────────────────────────────────────────────────────────────────
print("\n" + "="*65)
print("  Part1: get_negated_terms() 单元测试")
print("="*65)

cases_neg = [
    ("我没有发烧，但头很疼", {"发烧"}),
    ("没有胸痛，呼吸有点困难", {"胸痛"}),
    ("不是头疼，是脖子疼", {"头疼"}),
    ("无发热，腹痛三天", {"发热"}),
    ("我有发烧，头很疼", set()),   # 肯定句，无否定词
]

for text, expected_negated in cases_neg:
    negated = get_negated_terms(text)
    # 检查 expected_negated 中每个词是否都在 negated 中
    ok = all(e in negated for e in expected_negated)
    check(f"'{text}' → negated={negated}", ok,
          f"expected subset: {expected_negated}")

# ──────────────────────────────────────────────────────────────────────
print("\n" + "="*65)
print("  Part2: /api/analyze 否定症状不进入 structured.symptoms (API级)")
print("="*65)

negation_api_cases = [
    {
        "input": "我没有发烧，但头很疼三天了",
        "should_contain": ["头"],
        "should_not_contain": ["发烧", "发热"],
        "note": "发烧被否定，头疼保留"
    },
    {
        "input": "没有胸痛，但呼吸有点困难",
        "should_contain": ["呼吸"],          # fallback 提取为"呼吸困难"，含"呼吸"
        "should_not_contain": ["胸痛"],
        "note": "胸痛被否定，呼吸困难保留"
    },
    {
        "input": "不是头疼，是脖子疼",
        "should_contain": ["颈"],            # fallback 标准化为"颈部疼痛"，含"颈"
        "should_not_contain": ["头疼", "头痛"],
        "note": "头疼被否定，脖子(颈部)疼保留"
    },
]

for c in negation_api_cases:
    resp = client.post("/api/analyze", json={"user_input": c["input"]})
    data = resp.json()
    symptoms_raw = (data.get("structured") or {}).get("symptoms") or []
    acc_raw = (data.get("structured") or {}).get("accompanying_symptoms") or []
    all_symptoms_str = " ".join(symptoms_raw + acc_raw).lower()

    for should in c["should_contain"]:
        ok = should in all_symptoms_str
        check(f"'{c['note']}' — '{should}' 应存在于症状字段", ok,
              f"symptoms={symptoms_raw}")

    for should_not in c["should_not_contain"]:
        ok = should_not not in all_symptoms_str
        check(f"'{c['note']}' — '{should_not}' 不应出现在症状字段", ok,
              f"symptoms={symptoms_raw}")

# ──────────────────────────────────────────────────────────────────────
print("\n" + "="*65)
print("  Part3: '头疼' 触发 insufficient_symptom + needs_followup")
print("="*65)

# 后端验证
resp = client.post("/api/analyze", json={"user_input": "头疼"})
data = resp.json()
input_type = data.get("input_type")
needs_followup = data.get("needs_followup")
fq = data.get("followup_questions") or []

check(f"'头疼' → input_type=insufficient_symptom (got: {input_type})",
      input_type == "insufficient_symptom")
check(f"'头疼' → needs_followup=True (got: {needs_followup})",
      needs_followup is True)
check(f"'头疼' → followup_questions 不为空 (got: {len(fq)}条)",
      len(fq) > 0)

# 模拟追问后合并重分析
combined = "头疼\n补充：疼痛持续了多久？ → 是，三天了\n补充：严重程度如何？ → 中等程度，影响日常"
resp2 = client.post("/api/analyze", json={"user_input": combined})
data2 = resp2.json()
check(f"追问合并后 input_type=valid_symptom (got: {data2.get('input_type')})",
      data2.get("input_type") == "valid_symptom")
check(f"追问合并后 risk 不为空",
      data2.get("risk") is not None)

# ──────────────────────────────────────────────────────────────────────
print("\n" + "="*65)
print(f"  TOTAL: {passed}/{passed+failed} passed")
print("="*65)
sys.exit(0 if failed == 0 else 1)
