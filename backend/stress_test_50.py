"""
50条全面压测脚本 - 覆盖所有场景
阶段一：运行测试，记录结果
阶段二：找出所有错误
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 50条测试矩阵设计
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST_MATRIX = [

    # ─── EMERGENCY 场景（8条）─────────────────────────────────────
    {"id": 1,  "group": "EMERGENCY", "input": "被车撞了，头部受伤，大出血止不住",
     "expect_type": "valid_symptom", "expect_level": "EMERGENCY", "note": "交通事故+大出血"},

    {"id": 2,  "group": "EMERGENCY", "input": "胸口剧烈压榨感，出冷汗，感觉快不行了",
     "expect_type": "valid_symptom", "expect_level": "EMERGENCY", "note": "急性心梗典型表现"},

    {"id": 3,  "group": "EMERGENCY", "input": "突然说话不清楚，右侧手脚没力气，口角歪斜",
     "expect_type": "valid_symptom", "expect_level": "EMERGENCY", "note": "中风三联征"},

    {"id": 4,  "group": "EMERGENCY", "input": "吃了一大把安眠药，感觉很犯困",
     "expect_type": "valid_symptom", "expect_level": "EMERGENCY", "note": "药物过量中毒"},

    {"id": 5,  "group": "EMERGENCY", "input": "不想活了，准备好了方式",
     "expect_type": "valid_symptom", "expect_level": "EMERGENCY", "note": "自杀风险"},

    {"id": 6,  "group": "EMERGENCY", "input": "全身抽搐，口吐白沫，叫不醒",
     "expect_type": "valid_symptom", "expect_level": "EMERGENCY", "note": "癫痫持续状态"},

    {"id": 7,  "group": "EMERGENCY", "input": "喘不上气，喉咙里有东西堵住，呼吸很困难",
     "expect_type": "valid_symptom", "expect_level": "EMERGENCY", "note": "气道梗阻"},

    {"id": 8,  "group": "EMERGENCY", "input": "产后大出血，血一直流",
     "expect_type": "valid_symptom", "expect_level": "EMERGENCY", "note": "产后出血急症"},

    # ─── HIGH 风险（10条）─────────────────────────────────────────
    {"id": 9,  "group": "HIGH", "input": "持续高烧40度，已经烧了两天，退烧药没效果",
     "expect_type": "valid_symptom", "expect_level": "HIGH", "note": "持续高热"},

    {"id": 10, "group": "HIGH", "input": "右下腹剧烈疼痛，按压更痛，不敢动",
     "expect_type": "valid_symptom", "expect_level": "HIGH", "note": "疑似阑尾炎"},

    {"id": 11, "group": "HIGH", "input": "胸痛，有点气促，心跳加快，持续半小时了",
     "expect_type": "valid_symptom", "expect_level": "HIGH", "note": "胸痛+气促组合"},

    {"id": 12, "group": "HIGH", "input": "咳嗽痰中带血，持续一周，还有夜间盗汗",
     "expect_type": "valid_symptom", "expect_level": "HIGH", "note": "咯血+盗汗"},

    {"id": 13, "group": "HIGH", "input": "突然视力模糊，看东西重影，头很痛",
     "expect_type": "valid_symptom", "expect_level": "HIGH", "note": "神经系统症状"},

    {"id": 14, "group": "HIGH", "input": "尿血，小便带血，腰部疼痛",
     "expect_type": "valid_symptom", "expect_level": "HIGH", "note": "血尿+腰痛"},

    {"id": 15, "group": "HIGH", "input": "剧烈头痛突然发作，是我这辈子最疼的头痛",
     "expect_type": "valid_symptom", "expect_level": "HIGH", "note": "雷击样头痛"},

    {"id": 16, "group": "HIGH", "input": "小孩高烧39.5度，烧了一天，精神不好，不爱吃东西",
     "expect_type": "valid_symptom", "expect_level": "HIGH", "note": "儿童高热"},

    {"id": 17, "group": "HIGH", "input": "腹泻水样便，一天拉了十多次，头晕，嘴唇很干",
     "expect_type": "valid_symptom", "expect_level": "HIGH", "note": "严重腹泻脱水"},

    {"id": 18, "group": "HIGH", "input": "血压高到180，头晕头痛，恶心想吐",
     "expect_type": "valid_symptom", "expect_level": "HIGH", "note": "高血压危象"},

    # ─── MEDIUM 风险（12条）───────────────────────────────────────
    {"id": 19, "group": "MEDIUM", "input": "头疼三天了，昨晚发烧38.5度，还有点恶心",
     "expect_type": "valid_symptom", "expect_level": "MEDIUM", "note": "发热头疼恶心"},

    {"id": 20, "group": "MEDIUM", "input": "咳嗽两周了，有黄痰，低烧37.5",
     "expect_type": "valid_symptom", "expect_level": "MEDIUM", "note": "咳嗽+低烧"},

    {"id": 21, "group": "MEDIUM", "input": "肚子痛了几天，大便不正常，有点拉稀",
     "expect_type": "valid_symptom", "expect_level": "MEDIUM", "note": "腹痛腹泻"},

    {"id": 22, "group": "MEDIUM→HIGH", "input": "心慌心悸，感觉心跳很快，有点喘",
     "expect_type": "valid_symptom", "expect_level": "HIGH", "note": "心悸气促(心悸+喘→HIGH合理)"},

    {"id": 23, "group": "MEDIUM", "input": "眼睛和皮肤都有点发黄，尿颜色很深",
     "expect_type": "valid_symptom", "expect_level": "MEDIUM", "note": "黄疸症状"},

    {"id": 24, "group": "MEDIUM", "input": "尿频尿急，小便有灼热感，下腹隐痛",
     "expect_type": "valid_symptom", "expect_level": "MEDIUM", "note": "尿路感染"},

    {"id": 25, "group": "MEDIUM", "input": "月经很不规律，有时候两三个月不来，最近小腹隐痛",
     "expect_type": "valid_symptom", "expect_level": "MEDIUM", "note": "妇科-月经不调"},

    {"id": 26, "group": "MEDIUM", "input": "阴道异常分泌物，颜色发黄，有异味，外阴痒",
     "expect_type": "valid_symptom", "expect_level": "MEDIUM", "note": "妇科炎症"},

    {"id": 27, "group": "MEDIUM", "input": "皮肤出了很多红疹，痒得厉害，有点发烧",
     "expect_type": "valid_symptom", "expect_level": "MEDIUM", "note": "皮疹发热"},

    {"id": 28, "group": "MEDIUM", "input": "最近越来越焦虑，睡不着，头痛，心跳快",
     "expect_type": "valid_symptom", "expect_level": "MEDIUM", "note": "焦虑躯体化"},

    {"id": 29, "group": "MEDIUM", "input": "腰疼了好几天，弯腰困难，有时候腿也麻",
     "expect_type": "valid_symptom", "expect_level": "MEDIUM", "note": "腰痛+放射痛"},

    {"id": 30, "group": "MEDIUM", "input": "头晕目眩，天旋地转，站不稳，恶心",
     "expect_type": "valid_symptom", "expect_level": "MEDIUM", "note": "眩晕症状"},

    # ─── LOW 风险（10条）──────────────────────────────────────────
    {"id": 31, "group": "LOW", "input": "有点流鼻涕，轻微咳嗽，体温正常",
     "expect_type": "valid_symptom", "expect_level": "LOW", "note": "普通感冒轻症"},

    {"id": 32, "group": "LOW", "input": "感觉有点累，睡了一觉没精神",
     "expect_type": "valid_symptom", "expect_level": "LOW", "note": "轻度疲劳"},

    {"id": 33, "group": "LOW", "input": "吃多了有点胀，消化不太好",
     "expect_type": "valid_symptom", "expect_level": "LOW", "note": "消化不良"},

    {"id": 34, "group": "LOW", "input": "嗓子有点干，轻微喉咙痒",
     "expect_type": "valid_symptom", "expect_level": "LOW", "note": "轻症咽喉"},

    {"id": 35, "group": "LOW", "input": "有点失眠，偶尔入睡困难",
     "expect_type": "valid_symptom", "expect_level": "LOW", "note": "轻度失眠"},

    {"id": 36, "group": "LOW", "input": "最近工作压力大，有点焦虑，容易紧张",
     "expect_type": "valid_symptom", "expect_level": "LOW", "note": "压力焦虑"},

    {"id": 37, "group": "LOW", "input": "眼睛有点酸，看手机多了有些疲劳",
     "expect_type": "valid_symptom", "expect_level": "LOW", "note": "视疲劳"},

    {"id": 38, "group": "LOW", "input": "背有点酸，坐久了不舒服",
     "expect_type": "valid_symptom", "expect_level": "LOW", "note": "肌肉酸痛"},

    {"id": 39, "group": "LOW", "input": "有一点头疼，不厉害，可能是睡眠不好",
     "expect_type": "valid_symptom", "expect_level": "LOW", "note": "轻微头痛"},

    {"id": 40, "group": "LOW", "input": "皮肤有点干燥，轻微瘙痒",
     "expect_type": "valid_symptom", "expect_level": "LOW", "note": "皮肤干燥"},

    # ─── 非医疗输入（5条）────────────────────────────────────────
    {"id": 41, "group": "NON_MEDICAL", "input": "帮我写一段Python爬虫代码",
     "expect_type": "non_medical_input", "expect_level": None, "note": "编程问题"},

    {"id": 42, "group": "NON_MEDICAL", "input": "今天天气怎么样",
     "expect_type": "non_medical_input", "expect_level": None, "note": "日常闲聊"},

    {"id": 43, "group": "NON_MEDICAL", "input": "推荐几本AI产品经理的书",
     "expect_type": "non_medical_input", "expect_level": None, "note": "书单推荐"},

    {"id": 44, "group": "NON_MEDICAL", "input": "帮我优化这段SQL查询",
     "expect_type": "non_medical_input", "expect_level": None, "note": "数据库问题"},

    {"id": 45, "group": "NON_MEDICAL", "input": "这个月KPI完不成怎么办",
     "expect_type": "non_medical_input", "expect_level": None, "note": "工作烦恼"},

    # ─── 信息不足输入（5条）───────────────────────────────────────
    {"id": 46, "group": "INSUFFICIENT", "input": "感觉哪里不对",
     "expect_type": "insufficient_symptom", "expect_level": None, "note": "极度模糊"},

    {"id": 47, "group": "INSUFFICIENT", "input": "今天状态不太好",
     "expect_type": "insufficient_symptom", "expect_level": None, "note": "状态描述"},

    {"id": 48, "group": "INSUFFICIENT", "input": "有点不舒服",
     "expect_type": "insufficient_symptom", "expect_level": None, "note": "简单不适"},

    {"id": 49, "group": "INSUFFICIENT", "input": "感觉身体很怪",
     "expect_type": "insufficient_symptom", "expect_level": None, "note": "异常感"},

    {"id": 50, "group": "INSUFFICIENT", "input": "不太好",
     "expect_type": "insufficient_symptom", "expect_level": None, "note": "极简"},
]


def run_all_tests():
    results = []
    print("=" * 90)
    print("50条压测矩阵 - 开始执行")
    print("=" * 90)

    for case in TEST_MATRIX:
        resp = client.post("/api/analyze", json={"user_input": case["input"]})
        if resp.status_code != 200:
            results.append({**case,
                "actual_type": "ERROR", "actual_level": "ERROR",
                "has_followup": False, "pass": False, "error": resp.text[:80]})
            continue

        data = resp.json()
        actual_type  = data.get("input_type", "MISSING")
        actual_level = (data.get("risk") or {}).get("level") if data.get("risk") else None
        has_followup = bool(data.get("needs_followup") and data.get("followup_questions"))

        type_ok  = actual_type == case["expect_type"]
        level_ok = True  # default
        if case["expect_level"] is not None:
            # For EMERGENCY/HIGH: accept equal or higher (EMERGENCY satisfies HIGH expect too)
            rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "EMERGENCY": 3}
            if case["expect_level"] == "HIGH":
                level_ok = rank.get(actual_level, -1) >= rank["HIGH"]
            else:
                level_ok = actual_level == case["expect_level"]
        elif actual_level is not None and case["expect_type"] in ("non_medical_input", "insufficient_symptom"):
            # these cases should have NO risk data
            level_ok = actual_level is None  # will be False if level returned

        passed = type_ok and level_ok
        results.append({**case,
            "actual_type": actual_type,
            "actual_level": actual_level,
            "has_followup": has_followup,
            "type_ok": type_ok,
            "level_ok": level_ok,
            "pass": passed,
        })

    return results


def print_results(results):
    pass_count = sum(1 for r in results if r["pass"])
    fail_count = len(results) - pass_count

    # Summary table
    print(f"\n{'ID':>3} {'Group':12} {'Pass':5} {'ExpType':22} {'ActType':22} {'ExpLv':10} {'ActLv':10} {'Note'}")
    print("-" * 110)
    for r in results:
        ok = "PASS" if r["pass"] else "FAIL"
        exp_lv = str(r.get("expect_level") or "-")
        act_lv = str(r.get("actual_level") or "-")
        print(f"{r['id']:>3} {r['group']:12} {ok:5} {r['expect_type']:22} {r['actual_type']:22} {exp_lv:10} {act_lv:10} {r['note']}")

    print(f"\n{'='*90}")
    print(f"TOTAL: {pass_count}/{len(results)} passed  ({fail_count} failed)")
    print(f"{'='*90}")

    # Failures detail
    failures = [r for r in results if not r["pass"]]
    if failures:
        print("\n[FAILURES DETAIL]")
        for r in failures:
            print(f"\n  ID {r['id']} [{r['group']}] {r['note']}")
            print(f"    Input  : {r['input']}")
            print(f"    Expect : type={r['expect_type']}  level={r.get('expect_level')}")
            print(f"    Actual : type={r['actual_type']}  level={r.get('actual_level')}")
            if not r.get("type_ok"):
                print(f"    ERROR  : input_type mismatch")
            if not r.get("level_ok"):
                print(f"    ERROR  : risk_level mismatch")
    else:
        print("\n[ALL TESTS PASSED]")

    return failures


if __name__ == "__main__":
    results = run_all_tests()
    failures = print_results(results)
    sys.exit(0 if not failures else 1)
