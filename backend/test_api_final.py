"""最终API测试"""
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

test_cases = [
    ("被车撞了，大出血，血一直止不住", "EMERGENCY", 90),
    ("胸口像被压住一样，喘不上气，出了很多冷汗", "EMERGENCY", 85),
    ("突然说话不清楚，一侧手脚没力气，嘴也有点歪", "EMERGENCY", 85),
    ("我不想活了，想结束自己", "EMERGENCY", 85),
    ("有点流鼻涕，轻微咳嗽，体温正常", "LOW", 30),
    ("我感觉不太舒服", "LOW", 30),
    ("孕妇肚子很痛，还流血", "HIGH", 70),
]

print("="*80)
print("API Final Test")
print("="*80)

passed = 0
failed = 0

for text, expected_level, min_score in test_cases:
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
        level_match = (level == expected_level) or (level == "EMERGENCY" and expected_level in ["HIGH", "EMERGENCY"])
        score_match = score >= min_score
        
        if level_match and score_match:
            status = "[PASS]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1
        
        print(f"{status} Expected: {expected_level} (>={min_score}), Got: {level} ({score})")
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
