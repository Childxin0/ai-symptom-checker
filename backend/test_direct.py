"""直接测试风险引擎"""
from core.risk_engine import get_risk_engine

test_inputs = [
    "被车撞了，大出血，血一直止不住",
    "胸口像被压住一样，喘不上气，出了很多冷汗",
    "突然说话不清楚，一侧手脚没力气，嘴也有点歪",
    "我不想活了，想结束自己",
    "有点流鼻涕，轻微咳嗽，体温正常",
    "我感觉不太舒服",
    "孕妇肚子很痛，还流血",
]

engine = get_risk_engine()

for text in test_inputs:
    print(f"\n{'='*60}")
    print(f"输入: {text}")
    print(f"{'='*60}")
    risk = engine.evaluate(text, None)
    print(f"风险等级: {risk.level}")
    print(f"风险分数: {risk.score}")
    print(f"触发规则: {risk.triggered_rules}")
    print(f"规则解释: {risk.rule_explanations}")
