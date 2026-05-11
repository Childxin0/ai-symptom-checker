"""
回归测试：轻症感冒误判高风险修复
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _analyze(text: str):
    resp = client.post("/api/analyze", json={"user_input": text})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_cold_normal_temp_should_be_low():
    data = _analyze("有点流鼻涕，体温正常")
    assert data["risk"]["level"] == "LOW"
    assert data["risk"]["score"] <= 25
    assert data["urgency_timeline"] == "可观察"
    assert "急诊" not in data["recommended_department"]


def test_cold_cough_no_fever_should_be_low():
    data = _analyze("流鼻涕，轻微咳嗽，没有发烧")
    assert data["risk"]["level"] == "LOW"
    assert data["risk"]["score"] <= 25
    assert data["urgency_timeline"] == "可观察"
    assert "急诊" not in data["recommended_department"]


def test_cold_with_fever_38_should_be_medium():
    data = _analyze("流鼻涕发烧38度")
    assert data["risk"]["level"] == "MEDIUM"


def test_chest_pressure_breathing_sweat_should_be_high_or_emergency():
    data = _analyze("胸口像被压住，喘不上气，出冷汗")
    assert data["risk"]["level"] in ("HIGH", "EMERGENCY")

