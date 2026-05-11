"""
测试用例集 - 验证风险分层系统的准确性
覆盖 EMERGENCY / HIGH / MEDIUM / LOW 四个等级，涵盖多种急症场景
"""

from typing import List, Dict, Any
from services.risk_engine import evaluate_rules


class TestCase:
    """测试用例数据类"""
    def __init__(
        self,
        input_text: str,
        expected_level: str,
        expected_min_score: int,
        category: str,
        description: str,
        key_signals: List[str]
    ):
        self.input_text = input_text
        self.expected_level = expected_level
        self.expected_min_score = expected_min_score
        self.category = category
        self.description = description
        self.key_signals = key_signals


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EMERGENCY 级别测试用例 - 需要立即急救
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EMERGENCY_TEST_CASES = [
    TestCase(
        input_text="被车撞了 大出血",
        expected_level="EMERGENCY",
        expected_min_score=90,
        category="外伤急症",
        description="车祸外伤伴大出血",
        key_signals=["事故", "大量出血"]
    ),
    TestCase(
        input_text="刚才从楼梯上摔下来，头部着地，现在头很痛还流了很多血",
        expected_level="EMERGENCY",
        expected_min_score=90,
        category="外伤急症",
        description="高处坠落头部受伤",
        key_signals=["坠落", "头部受伤", "出血"]
    ),
    TestCase(
        input_text="胸口像被压住一样，喘不上气，出了很多冷汗",
        expected_level="EMERGENCY",
        expected_min_score=90,
        category="心血管急症",
        description="疑似急性心梗",
        key_signals=["胸痛压榨感", "呼吸困难"]
    ),
    TestCase(
        input_text="突然说话不清楚，一侧手脚没力气，嘴巴有点歪",
        expected_level="EMERGENCY",
        expected_min_score=90,
        category="神经系统急症",
        description="中风征兆",
        key_signals=["言语不清", "单侧无力", "面瘫"]
    ),
    TestCase(
        input_text="意识不清，叫不醒，刚才还晕倒了",
        expected_level="EMERGENCY",
        expected_min_score=90,
        category="神经系统急症",
        description="意识障碍",
        key_signals=["意识不清", "晕倒"]
    ),
    TestCase(
        input_text="吃了海鲜后全身起红疹，喉咙肿胀，呼吸有点困难",
        expected_level="EMERGENCY",
        expected_min_score=90,
        category="过敏急症",
        description="严重过敏反应",
        key_signals=["喉头水肿", "呼吸困难"]
    ),
    TestCase(
        input_text="我不想活了，准备自杀",
        expected_level="EMERGENCY",
        expected_min_score=90,
        category="心理危机",
        description="自杀倾向",
        key_signals=["自杀意念"]
    ),
    TestCase(
        input_text="误喝了农药，现在很难受",
        expected_level="EMERGENCY",
        expected_min_score=90,
        category="中毒急症",
        description="农药中毒",
        key_signals=["中毒"]
    ),
    TestCase(
        input_text="怀孕6个月，突然肚子很痛，还有阴道大出血",
        expected_level="EMERGENCY",
        expected_min_score=90,
        category="孕产妇急症",
        description="孕期大出血",
        key_signals=["孕期", "大出血"]
    ),
    TestCase(
        input_text="一直吐血，止不住，流了很多",
        expected_level="EMERGENCY",
        expected_min_score=90,
        category="出血急症",
        description="大量呕血",
        key_signals=["呕血", "流血不止"]
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HIGH 级别测试用例 - 高危风险，需尽快就医
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HIGH_TEST_CASES = [
    TestCase(
        input_text="右下腹剧烈疼痛，按压更痛，疼了8小时了",
        expected_level="HIGH",
        expected_min_score=70,
        category="急腹症",
        description="疑似阑尾炎",
        key_signals=["右下腹痛", "剧烈疼痛"]
    ),
    TestCase(
        input_text="胸痛，喘不过气，感觉胸闷得很",
        expected_level="HIGH",
        expected_min_score=70,
        category="心血管",
        description="胸痛伴呼吸困难",
        key_signals=["胸痛", "呼吸困难"]
    ),
    TestCase(
        input_text="头痛得很厉害，痛了一整天，越来越严重",
        expected_level="HIGH",
        expected_min_score=70,
        category="神经系统",
        description="剧烈头痛",
        key_signals=["剧烈头痛"]
    ),
    TestCase(
        input_text="高烧40度，身体发抖，寒战得厉害",
        expected_level="HIGH",
        expected_min_score=70,
        category="感染",
        description="高热伴寒战",
        key_signals=["高烧", "寒战"]
    ),
    TestCase(
        input_text="小便带血，尿血很明显",
        expected_level="HIGH",
        expected_min_score=70,
        category="泌尿系统",
        description="血尿",
        key_signals=["尿血"]
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MEDIUM 级别测试用例 - 中等风险，建议就医
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MEDIUM_TEST_CASES = [
    TestCase(
        input_text="头疼三天了，昨晚发烧38.5度，有点恶心",
        expected_level="MEDIUM",
        expected_min_score=40,
        category="发热症状",
        description="持续发热伴头痛",
        key_signals=["发热", "持续头痛", "呕吐"]
    ),
    TestCase(
        input_text="反复呕吐，吃什么吐什么，已经一天了",
        expected_level="MEDIUM",
        expected_min_score=40,
        category="消化系统",
        description="反复呕吐",
        key_signals=["反复呕吐"]
    ),
    TestCase(
        input_text="心慌心跳快，感觉心脏跳得很不舒服",
        expected_level="MEDIUM",
        expected_min_score=40,
        category="心血管",
        description="心悸症状",
        key_signals=["心悸", "心跳快"]
    ),
    TestCase(
        input_text="拉肚子很严重，水样便，一天拉了十几次",
        expected_level="MEDIUM",
        expected_min_score=40,
        category="消化系统",
        description="严重腹泻",
        key_signals=["严重腹泻"]
    ),
    TestCase(
        input_text="皮肤发黄，眼睛也有点黄，尿很黄",
        expected_level="MEDIUM",
        expected_min_score=40,
        category="肝胆",
        description="黄疸症状",
        key_signals=["黄疸"]
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOW 级别测试用例 - 低风险，可观察
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOW_TEST_CASES = [
    TestCase(
        input_text="有点流鼻涕，轻微咳嗽，应该是感冒了",
        expected_level="LOW",
        expected_min_score=10,
        category="轻症",
        description="普通感冒症状",
        key_signals=["流鼻涕", "轻微咳嗽"]
    ),
    TestCase(
        input_text="有点头疼，可能是昨晚没睡好",
        expected_level="LOW",
        expected_min_score=10,
        category="轻症",
        description="轻度头痛",
        key_signals=["轻微头痛"]
    ),
    TestCase(
        input_text="感觉有点累，可能工作压力大",
        expected_level="LOW",
        expected_min_score=10,
        category="轻症",
        description="轻度疲劳",
        key_signals=["疲劳"]
    ),
    TestCase(
        input_text="胃有点胀，可能是吃多了",
        expected_level="LOW",
        expected_min_score=10,
        category="轻症",
        description="轻度消化不良",
        key_signals=["胃胀"]
    ),
    TestCase(
        input_text="眼睛有点干，看电脑太久了",
        expected_level="LOW",
        expected_min_score=10,
        category="轻症",
        description="视疲劳",
        key_signals=["眼睛干涩"]
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 测试执行函数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_test_case(test_case: TestCase) -> Dict[str, Any]:
    """执行单个测试用例"""
    risk_level, risk_score, rule_triggered, hints = evaluate_rules(test_case.input_text)
    
    passed = (
        risk_level == test_case.expected_level and
        risk_score >= test_case.expected_min_score
    )
    
    return {
        "input": test_case.input_text,
        "category": test_case.category,
        "description": test_case.description,
        "expected_level": test_case.expected_level,
        "actual_level": risk_level,
        "expected_min_score": test_case.expected_min_score,
        "actual_score": risk_score,
        "triggered_rules": rule_triggered,
        "key_signals": test_case.key_signals,
        "identified_signals": hints,
        "passed": passed,
    }


def run_all_tests() -> Dict[str, Any]:
    """运行所有测试用例"""
    all_tests = [
        ("EMERGENCY", EMERGENCY_TEST_CASES),
        ("HIGH", HIGH_TEST_CASES),
        ("MEDIUM", MEDIUM_TEST_CASES),
        ("LOW", LOW_TEST_CASES),
    ]
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "by_level": {},
    }
    
    for level_name, test_cases in all_tests:
        level_results = {
            "total": len(test_cases),
            "passed": 0,
            "failed": 0,
            "cases": []
        }
        
        for test_case in test_cases:
            result = run_test_case(test_case)
            level_results["cases"].append(result)
            
            if result["passed"]:
                level_results["passed"] += 1
                results["passed"] += 1
            else:
                level_results["failed"] += 1
                results["failed"] += 1
            
            results["total"] += 1
        
        results["by_level"][level_name] = level_results
    
    return results


def print_test_results(results: Dict[str, Any]):
    """打印测试结果"""
    print("=" * 80)
    print("[TEST] 风险分层系统测试报告")
    print("=" * 80)
    print(f"\n总计: {results['total']} 个测试用例")
    print(f"[PASS] 通过: {results['passed']}")
    print(f"[FAIL] 失败: {results['failed']}")
    print(f"[RATE] 通过率: {results['passed'] / results['total'] * 100:.1f}%\n")
    
    for level_name, level_results in results["by_level"].items():
        print(f"\n{'━' * 80}")
        print(f"【{level_name} 级别测试】")
        print(f"{'━' * 80}")
        print(f"通过: {level_results['passed']}/{level_results['total']}")
        
        for i, case in enumerate(level_results["cases"], 1):
            status = "[OK]" if case["passed"] else "[!!]"
            print(f"\n{status} 测试 {i}: {case['description']}")
            print(f"   输入: {case['input'][:50]}...")
            print(f"   预期: {case['expected_level']} (>={case['expected_min_score']}分)")
            print(f"   实际: {case['actual_level']} ({case['actual_score']}分)")
            
            if not case["passed"]:
                print(f"   [WARN] 测试失败原因:")
                if case['actual_level'] != case['expected_level']:
                    print(f"      - 风险等级不匹配: 预期 {case['expected_level']}, 实际 {case['actual_level']}")
                if case['actual_score'] < case['expected_min_score']:
                    print(f"      - 风险分数过低: 预期 >={case['expected_min_score']}, 实际 {case['actual_score']}")
            
            print(f"   识别信号: {', '.join(case['identified_signals'][:3])}")
    
    print(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    results = run_all_tests()
    print_test_results(results)
