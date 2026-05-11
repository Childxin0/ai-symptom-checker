"""
测试状态冲突修复 - 验证三种input_type的完整渲染链路
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_complete_rendering_chain():
    """测试完整的渲染链路：非医疗输入、信息不足、有效症状"""
    
    test_cases = [
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 非医疗输入 (3个测试)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {
            "id": 1,
            "input": "更好的升级方向：做成AI医疗PM面试杀器版",
            "expected_type": "non_medical_input",
            "should_have_risk": False,
            "should_have_structured": False,
            "description": "项目规划文本"
        },
        {
            "id": 2,
            "input": "帮我写一段AI PM简历项目经历",
            "expected_type": "non_medical_input",
            "should_have_risk": False,
            "should_have_structured": False,
            "description": "简历讨论"
        },
        {
            "id": 3,
            "input": "这个项目怎么部署到Vercel",
            "expected_type": "non_medical_input",
            "should_have_risk": False,
            "should_have_structured": False,
            "description": "技术问题"
        },
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 信息不足 (3个测试)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {
            "id": 4,
            "input": "我不舒服",
            "expected_type": "insufficient_symptom",
            "should_have_risk": False,
            "should_have_structured": False,
            "should_have_followup": True,
            "description": "模糊症状"
        },
        {
            "id": 5,
            "input": "身体有点怪",
            "expected_type": "insufficient_symptom",
            "should_have_risk": False,
            "should_have_structured": False,
            "should_have_followup": True,
            "description": "模糊不适"
        },
        {
            "id": 6,
            "input": "难受",
            "expected_type": "insufficient_symptom",
            "should_have_risk": False,
            "should_have_structured": False,
            "should_have_followup": True,
            "description": "极简输入"
        },
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 有效症状 (3个测试)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {
            "id": 7,
            "input": "头疼三天，昨晚发烧38.5度，还有点恶心",
            "expected_type": "valid_symptom",
            "should_have_risk": True,
            "should_have_structured": True,
            "expected_risk_level": ["MEDIUM", "HIGH"],
            "expected_symptoms": ["头疼", "头痛", "发烧", "发热", "恶心"],
            "should_have_duration": True,
            "description": "完整症状描述"
        },
        {
            "id": 8,
            "input": "头被车撞了，大出血，血一直止不住",
            "expected_type": "valid_symptom",
            "should_have_risk": True,
            "should_have_structured": True,
            "expected_risk_level": ["EMERGENCY"],
            "min_score": 85,
            "description": "紧急外伤"
        },
        {
            "id": 9,
            "input": "有点流鼻涕，轻微咳嗽，体温正常",
            "expected_type": "valid_symptom",
            "should_have_risk": True,
            "should_have_structured": True,
            "expected_risk_level": ["LOW"],
            "expected_symptoms": ["流鼻涕", "鼻涕", "咳嗽"],
            "description": "轻症感冒"
        },
    ]
    
    print("=" * 80)
    print("状态冲突修复 - 完整渲染链路测试")
    print("=" * 80)
    
    passed = 0
    failed = 0
    warnings = 0
    
    for case in test_cases:
        print(f"\n[TEST {case['id']}] {case['description']}")
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
        has_risk = result.get("risk") is not None
        has_structured = result.get("structured") is not None
        
        # 验证 input_type
        if actual_type != case["expected_type"]:
            print(f"  [FAIL] input_type: got {actual_type}, expected {case['expected_type']}")
            failed += 1
            continue
        
        print(f"  [PASS] input_type: {actual_type}")
        
        # 验证是否应该有 risk 数据
        if case.get("should_have_risk", False):
            if not has_risk:
                print(f"  [FAIL] Should have risk data but got None")
                failed += 1
                continue
            
            risk_level = result["risk"]["level"]
            risk_score = result["risk"]["score"]
            
            if "expected_risk_level" in case:
                if risk_level in case["expected_risk_level"]:
                    print(f"  [PASS] Risk Level: {risk_level} (score: {risk_score})")
                else:
                    print(f"  [FAIL] Risk Level: {risk_level}, expected one of {case['expected_risk_level']}")
                    failed += 1
                    continue
            
            if "min_score" in case:
                if risk_score >= case["min_score"]:
                    print(f"  [PASS] Risk Score: {risk_score} >= {case['min_score']}")
                else:
                    print(f"  [FAIL] Risk Score: {risk_score} < {case['min_score']}")
                    failed += 1
                    continue
        else:
            if has_risk:
                print(f"  [FAIL] Should NOT have risk data but got: {result['risk']}")
                failed += 1
                continue
            print(f"  [PASS] No risk data (as expected)")
        
        # 验证是否应该有 structured 数据
        if case.get("should_have_structured", False):
            if not has_structured:
                print(f"  [FAIL] Should have structured data but got None")
                failed += 1
                continue
            
            # 验证症状识别
            if "expected_symptoms" in case:
                symptoms = result["structured"].get("symptoms", [])
                symptoms_lower = [s.lower() for s in symptoms]
                matched = False
                for expected in case["expected_symptoms"]:
                    if any(expected.lower() in s for s in symptoms_lower):
                        matched = True
                        break
                
                if matched:
                    print(f"  [PASS] Symptoms: {', '.join(symptoms)}")
                else:
                    print(f"  [WARN] Symptoms: {', '.join(symptoms)}")
                    print(f"         Expected one of: {case['expected_symptoms']}")
                    warnings += 1
            
            # 验证 duration 识别
            if case.get("should_have_duration", False):
                duration = result["structured"].get("duration", "")
                if duration and duration not in ["未知", "未明确说明"]:
                    print(f"  [PASS] Duration: {duration}")
                else:
                    print(f"  [WARN] Duration: {duration} (should be more specific)")
                    warnings += 1
        else:
            if has_structured:
                print(f"  [FAIL] Should NOT have structured data")
                failed += 1
                continue
            print(f"  [PASS] No structured data (as expected)")
        
        # 验证追问
        if case.get("should_have_followup", False):
            if result.get("needs_followup") and result.get("followup_questions"):
                print(f"  [PASS] Has followup questions ({len(result['followup_questions'])} questions)")
            else:
                print(f"  [WARN] Should have followup questions")
                warnings += 1
        
        passed += 1
    
    print(f"\n{'=' * 80}")
    print(f"Results:")
    print(f"  Passed: {passed}/{len(test_cases)}")
    print(f"  Failed: {failed}/{len(test_cases)}")
    print(f"  Warnings: {warnings}")
    print(f"{'=' * 80}")
    
    if failed == 0:
        print("\n[SUCCESS] All critical tests passed!")
        if warnings > 0:
            print(f"[INFO] {warnings} warnings (non-critical issues)")
    else:
        print(f"\n[FAILURE] {failed} tests failed")
    
    return passed, failed, warnings


if __name__ == "__main__":
    passed, failed, warnings = test_complete_rendering_chain()
    sys.exit(0 if failed == 0 else 1)
