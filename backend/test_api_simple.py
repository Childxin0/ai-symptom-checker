"""简单API测试"""
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

test_cases = [
    "被车撞了，大出血，血一直止不住",
    "胸口像被压住一样，喘不上气，出了很多冷汗",
    "突然说话不清楚，一侧手脚没力气，嘴也有点歪",
    "我不想活了，想结束自己",
    "有点流鼻涕，轻微咳嗽，体温正常",
    "我感觉不太舒服",
    "孕妇肚子很痛，还流血",
]

print("="*80)
print("API 测试结果")
print("="*80)

for text in test_cases:
    print(f"\n{'─'*80}")
    print(f"输入: {text}")
    print(f"{'─'*80}")
    
    response = client.post("/api/analyze", json={"user_input": text})
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        risk = data.get("risk", {})
        print(f"风险等级: {risk.get('level', '未知')}")
        print(f"风险分数: {risk.get('score', 0)}")
        print(f"触发规则: {risk.get('triggered_rules', [])[:3]}")
        print(f"建议: {data.get('advice', '')[:100]}...")
        print(f"推荐科室: {data.get('recommended_department', '')}")
        print(f"LLM使用: {data.get('llm_used', False)}")
        if data.get('fallback_reason'):
            print(f"⚠️ Fallback原因: {data.get('fallback_reason')}")
    else:
        print(f"错误: {response.text[:200]}")
