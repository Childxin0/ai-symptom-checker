"""最终API测试"""
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

test_cases = [
    # 关键回归：轻症感冒 + 无发热
    ("有点流鼻涕，体温正常", "LOW", {"max_score": 25}),
    ("流鼻涕，轻微咳嗽，没有发烧", "LOW", {"max_score": 25}),
    ("流鼻涕发烧38度", "MEDIUM", {}),
    ("头疼三天，昨晚发烧38.5度", "MEDIUM_OR_HIGHER", {}),
    ("胸口像被压住，喘不上气，出冷汗", "HIGH_OR_EMERGENCY", {}),
]

print("="*80)
print("API Final Test")
print("="*80)

passed = 0
failed = 0

for text, expected_level, extra in test_cases:
    print(f"\n{'-'*80}")
    print(f"Input: {text}")
    print(f"{'-'*80}")
    
    response = client.post("/api/analyze", json={"user_input": text})
    
    if response.status_code == 200:
        data = response.json()
        risk = data.get("risk", {})
        level = risk.get('level', '?')
        score = risk.get('score', 0)
        
        # Check
        if expected_level == "HIGH_OR_EMERGENCY":
            level_match = level in ("HIGH", "EMERGENCY")
        elif expected_level == "MEDIUM_OR_HIGHER":
            level_match = level in ("MEDIUM", "HIGH", "EMERGENCY")
        else:
            level_match = level == expected_level

        max_score = extra.get("max_score")
        score_match = True if max_score is None else score <= max_score
        
        if level_match and score_match:
            status = "[PASS]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1
        
        expect_score_text = f"<= {max_score}" if max_score is not None else "N/A"
        print(f"{status} Expected level: {expected_level}, score: {expect_score_text}; Got: {level} ({score})")
        print(f"Rules: {', '.join(risk.get('triggered_rules', [])[:3])}")
        print(f"Dept: {data.get('recommended_department', '')}")
        print(f"Timeline: {data.get('urgency_timeline', '')}")
    else:
        print(f"[ERROR] Status: {response.status_code}")
        failed += 1

print(f"\n{'='*80}")
print(f"Results: {passed} passed, {failed} failed")
print(f"Pass rate: {passed/(passed+failed)*100:.1f}%")
print(f"{'='*80}")
