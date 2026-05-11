"""
测试输入意图识别功能
验证API能否正确处理三种输入类型
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_input_recognition():
    """测试输入意图识别"""
    
    test_cases = [
        # 非医疗输入
        {
            "input": "更好的升级方向：做成AI医疗PM面试杀器版",
            "expected_type": "non_medical_input",
            "description": "项目规划文本"
        },
        {
            "input": "帮我写简历",
            "expected_type": "non_medical_input",
            "description": "简历讨论"
        },
        {
            "input": "这个项目怎么部署到Vercel",
            "expected_type": "non_medical_input",
            "description": "技术问题"
        },
        
        # 信息不足
        {
            "input": "我感觉不太舒服",
            "expected_type": "insufficient_symptom",
            "description": "模糊描述"
        },
        {
            "input": "不舒服",
            "expected_type": "insufficient_symptom",
            "description": "过于简短"
        },
        {
            "input": "身体有点怪",
            "expected_type": "insufficient_symptom",
            "description": "信息不足"
        },
        
        # 有效症状
        {
            "input": "头疼三天，发烧38.5度，恶心",
            "expected_type": "valid_symptom",
            "expected_risk": ["MEDIUM", "HIGH"],
            "description": "完整症状描述"
        },
        {
            "input": "被车撞了，大出血",
            "expected_type": "valid_symptom",
            "expected_risk": ["EMERGENCY"],
            "description": "紧急外伤"
        },
        {
            "input": "胸口剧烈疼痛，喘不上气",
            "expected_type": "valid_symptom",
            "expected_risk": ["HIGH", "EMERGENCY"],
            "description": "高危症状"
        },
    ]
    
    print("=" * 80)
    print("输入意图识别 API 测试")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for case in test_cases:
        print(f"\n[TEST] {case['description']}")
        print(f"  Input: {case['input']}")
        print(f"  Expected Type: {case['expected_type']}")
        
        # 调用API
        response = client.post("/api/analyze", json={"user_input": case["input"]})
        
        if response.status_code != 200:
            print(f"  [FAIL] HTTP {response.status_code}")
            print(f"  Error: {response.text}")
            failed += 1
            continue
        
        result = response.json()
        actual_type = result.get("input_type")
        
        # 验证input_type
        if actual_type == case["expected_type"]:
            print(f"  [PASS] Got: {actual_type}")
            
            # 对于有效症状，进一步验证风险等级
            if actual_type == "valid_symptom" and "expected_risk" in case:
                risk_level = result.get("risk", {}).get("level")
                if risk_level in case["expected_risk"]:
                    print(f"  [PASS] Risk Level: {risk_level}")
                else:
                    print(f"  [WARN] Risk Level: {risk_level} (expected one of {case['expected_risk']})")
            
            # 对于非医疗输入，验证不应该有风险评估
            if actual_type == "non_medical_input":
                if result.get("risk") is None and result.get("structured") is None:
                    print(f"  [PASS] No risk/structured data (as expected)")
                else:
                    print(f"  [WARN] Should not have risk/structured data for non_medical_input")
            
            # 对于信息不足，验证是否有追问
            if actual_type == "insufficient_symptom":
                if result.get("needs_followup") and result.get("followup_questions"):
                    print(f"  [PASS] Has followup questions ({len(result['followup_questions'])} questions)")
                else:
                    print(f"  [WARN] Should have followup questions for insufficient_symptom")
            
            passed += 1
        else:
            print(f"  [FAIL] Got: {actual_type}")
            if result.get("input_validation_message"):
                print(f"  Message: {result['input_validation_message'][:80]}...")
            failed += 1
    
    print(f"\n{'=' * 80}")
    print(f"Results: {passed} passed, {failed} failed (Total: {passed + failed})")
    print(f"{'=' * 80}")
    
    return passed, failed


if __name__ == "__main__":
    passed, failed = test_input_recognition()
    sys.exit(0 if failed == 0 else 1)
