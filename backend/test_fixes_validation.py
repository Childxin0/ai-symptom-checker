"""
验证修复效果
1. 中英文混输（chest pain → EMERGENCY）
2. 口语化表达（心脏要跳出来 → HIGH/EMERGENCY）
3. 否定句过滤（没有发烧但头很疼 → 发烧不命中）
4. 追问流程（多轮合并文本分析）
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.text_preprocessor import preprocess_for_matching, filter_negations
from core.input_validator import validate_input
from core.risk_engine import evaluate_rules
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if detail:
        print(f"         {detail}")
    return condition


# ──────────────────────────────────────────────────────────────────────
# 测试1：中英文混输
# ──────────────────────────────────────────────────────────────────────
section("问题1：中英文混输识别")

cases_en = [
    ("我 chest pain 很严重，出冷汗", "EMERGENCY"),
    ("I have fever and headache", "MEDIUM"),
    ("感觉 dizzy，有点 nausea", "LOW"),        # 轻度：LOW/MEDIUM 均可接受
    ("shortness of breath，呼吸很难", "EMERGENCY"),
    ("palpitations，心跳很快", "MEDIUM"),
]

all_pass = True
for text, expect_level in cases_en:
    processed = preprocess_for_matching(text)
    level, score, rules, _ = evaluate_rules(text)   # engine 内部已预处理
    ok = level == expect_level or \
         (expect_level == "HIGH" and level in ("HIGH","EMERGENCY")) or \
         (expect_level == "MEDIUM" and level in ("MEDIUM","HIGH","EMERGENCY"))
    all_pass = check(f"{text[:35]:<35} → {level:9} (expect≥{expect_level})", ok,
                     f"preprocessed: {processed[:60]}") and all_pass

# ──────────────────────────────────────────────────────────────────────
# 测试2：口语化表达
# ──────────────────────────────────────────────────────────────────────
section("问题2：口语化表达识别")

cases_colloquial = [
    ("感觉心脏要跳出来了，手发麻", "HIGH"),     # 心悸+麻 → HIGH
    ("头要炸了，剧烈头痛", "HIGH"),             # 剧烈头痛 → HIGH（霹雳样才是EMERGENCY）
    ("喘不上来气，喉咙堵", "EMERGENCY"),        # 呼吸困难 → EMERGENCY
    ("快晕过去了，眼前发黑", "EMERGENCY"),      # 晕过去 → EMERGENCY
    ("胸口像被压住，出冷汗", "EMERGENCY"),      # 压榨感+出冷汗 → EMERGENCY
]

for text, expect_level in cases_colloquial:
    processed = preprocess_for_matching(text)
    level, score, rules, _ = evaluate_rules(text)
    ok = level == expect_level or \
         (expect_level == "HIGH" and level in ("HIGH","EMERGENCY"))
    all_pass = check(f"{text[:35]:<35} → {level:9} (expect≥{expect_level})", ok,
                     f"preprocessed: {processed[:60]}") and all_pass

# ──────────────────────────────────────────────────────────────────────
# 测试3：否定句过滤
# ──────────────────────────────────────────────────────────────────────
section("问题3：否定句过滤")

negation_cases = [
    ("我没有发烧，但头很疼",     "发烧", False),   # 发烧被否定，不应命中
    ("没有胸痛，但呼吸有点困难",  "胸痛", False),   # 胸痛被否定
    ("无发热，腹痛三天",          "发热", False),   # 无发热
    ("我有发烧，头很疼",          "发烧", True),    # 正常肯定句，应命中
]

for text, denied_symptom, should_hit in negation_cases:
    processed = preprocess_for_matching(text)
    # 检查预处理后是否含有被否定的症状词
    actually_hit = denied_symptom in processed
    if should_hit:
        ok = actually_hit
        label = f"肯定句：'{denied_symptom}' 应保留"
    else:
        ok = not actually_hit
        label = f"否定句：'{denied_symptom}' 应被移除"
    all_pass = check(f"{text:<30} | {label}", ok,
                     f"preprocessed: {processed[:60]}") and all_pass

# 额外验证：否定句过滤后风险等级是否合理
text_neg = "我没有发烧，但头很疼"
level, score, _, _ = evaluate_rules(text_neg)
# 头疼 → 至少LOW，但发烧应被过滤所以不会升到HIGH
not_over = level in ("LOW", "MEDIUM", "HIGH")   # 不因发烧误升EMERGENCY
ok = not_over and level != "EMERGENCY"
all_pass = check(f"'{text_neg}' → level={level} (不因误命中发烧而过高)", ok) and all_pass

# ──────────────────────────────────────────────────────────────────────
# 测试4：追问合并文本流程
# ──────────────────────────────────────────────────────────────────────
section("问题4：追问合并重新分析（API级）")

# 模拟：原始输入信息不足 → 追问 → 合并后变为 valid_symptom
original = "头疼"
resp1 = client.post("/api/analyze", json={"user_input": original})
data1 = resp1.json()
ok = data1.get("input_type") in ("insufficient_symptom", "valid_symptom")
all_pass = check(f"Step1 '头疼' input_type={data1.get('input_type')}", ok) and all_pass

# 模拟用户回答追问：补充信息后合并
combined = "头疼\n补充：疼痛持续了多久？ → 三天了，而且越来越严重\n补充：还有其他症状吗？ → 有点发烧38度，恶心"
resp2 = client.post("/api/analyze", json={"user_input": combined})
data2 = resp2.json()
ok2 = data2.get("input_type") == "valid_symptom"
ok3 = (data2.get("risk") or {}).get("level") in ("MEDIUM", "HIGH", "EMERGENCY")
all_pass = check(f"Step2 合并后 input_type={data2.get('input_type')}", ok2) and all_pass
all_pass = check(f"Step2 合并后 risk_level={(data2.get('risk') or {}).get('level')} (≥MEDIUM)", ok3) and all_pass

# 最终结果
section("汇总")
print(f"  {'[ALL PASS]' if all_pass else '[SOME FAILED]'}")
sys.exit(0 if all_pass else 1)
