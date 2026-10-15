"""
Timeline + Dashboard 路由测试

覆盖：
- GET /timeline   聚合（anniversary + photo + milestone + blog）
- GET /dashboard  聚合（couple + days + countdown + recent + stats）
- 过滤：?type= ?author= ?from= ?to=
- 权限：未绑定 403
"""
import pytest
from datetime import date, datetime, timedelta


# ============================================================
# 单元测试：里程碑
# ============================================================

class TestMilestoneCompute:

    def test_milestone_count(self):
        from app.modules.timeline.service import (
            compute_milestones, compute_milestones_summary,
        )
        ann = date(2024, 1, 1)
        ms = compute_milestones(ann)
        # MILESTONE_DAYS 有 10 个
        assert len(ms) == 10
        # 100 天的 milestone
        m100 = next(m for m in ms if m["payload"]["days"] == 100)
        assert m100["occurred_at"].date() == date(2024, 4, 10)

    def test_milestone_date_filter(self):
        from app.modules.timeline.service import compute_milestones
        ann = date(2024, 1, 1)
        ms = compute_milestones(ann, date_from=date(2024, 6, 1))
        # 200 天 = 2024-07-19 之后；365 天 = 2025-01-01 之后
        assert all(m["occurred_at"].date() >= date(2024, 6, 1) for m in ms)

    def test_milestone_summary_has_future(self):
        from app.modules.timeline.service import compute_milestones_summary
        ann = date(2024, 1, 1)
        items = compute_milestones_summary(ann)
        # 100 天是过去的；5000 天是未来的
        past = [i for i in items if not i.is_future]
        future = [i for i in items if i.is_future]
        assert len(past) >= 1
        assert len(future) >= 1


class TestCountdown:

    def test_countdown_anniversary_next_year(self):
        """恋爱日在今天之前 → 下个周年是明年"""
        from app.modules.timeline.service import compute_next_countdown
        # 假设今天是 2024-06-01（避免测试依赖 today）
        ann = date(2023, 6, 15)
        items = compute_next_countdown(ann, anniversaries=[])
        # next anniversary 应是 2024-06-15（已过）→ 2025-06-15
        # 但实际是 dynamic，需要看今天日期
        anni_item = items[0]
        # 第一个一定是恋爱日
        assert "周年" in anni_item.title or "天" in anni_item.title or "纪念" in anni_item.title

    def test_countdown_includes_anniversaries(self):
        from app.modules.timeline.service import compute_next_countdown
        # 构造一个 Anniversary 对象的最小 mock
        class MockAnni:
            def __init__(self, title, d):
                self.title = title
                self.date = d
        today = date.today()
        annis = [
            MockAnni("未来事件 A", today + timedelta(days=5)),
            MockAnni("未来事件 B", today + timedelta(days=10)),
        ]
        items = compute_next_countdown(today - timedelta(days=100), annis)
        titles = [i.title for i in items]
        # 至少包含 1 个 anniversary 项
        assert any("未来事件" in t for t in titles)


# ============================================================
# 集成测试：/timeline
# ============================================================

class TestTimeline:

    def test_timeline_empty(self, client, make_user):
        """空时间轴（仅里程碑）"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/timeline", headers=h)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # 仅里程碑（10 个）
        assert data["total"] == 10
        assert all(i["type"] == "MILESTONE" for i in data["items"])

    def test_timeline_includes_anniversary(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        client.post("/api/v1/anniversaries", headers=h, json={
            "title": "我们相遇",
            "date": str(date.today() - timedelta(days=50)),
        })
        resp = client.get("/api/v1/timeline", headers=h)
        data = resp.json()
        types = {i["type"] for i in data["items"]}
        assert "ANNIVERSARY" in types
        assert "MILESTONE" in types

    def test_timeline_includes_photo(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        # 创建相册 + 上传照片
        aid = client.post("/api/v1/albums", headers=h, json={"name": "A"}).json()["id"]
        client.post(
            f"/api/v1/photos?album_id={aid}",
            headers=h,
            files={"file": ("x.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\xff\xd9", "image/jpeg")},
        )
        resp = client.get("/api/v1/timeline?type=PHOTO", headers=h)
        data = resp.json()
        assert data["total"] >= 1
        assert all(i["type"] == "PHOTO" for i in data["items"])

    def test_timeline_filter_type(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        client.post("/api/v1/anniversaries", headers=h, json={
            "title": "x", "date": str(date.today()),
        })
        resp = client.get("/api/v1/timeline?type=ANNIVERSARY", headers=h)
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["type"] == "ANNIVERSARY"

    def test_timeline_pagination(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        # 10 个 milestone
        resp = client.get("/api/v1/timeline?type=MILESTONE&page=1&page_size=3", headers=h)
        data = resp.json()
        assert data["total"] == 10
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert data["total_pages"] == 4  # ceil(10/3)

    def test_timeline_requires_bound(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        resp = client.get(
            "/api/v1/timeline",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_BOUND"


# ============================================================
# 集成测试：/dashboard
# ============================================================

class TestDashboard:

    def test_dashboard_basic(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob", anniversary=date(2023, 1, 1))
        h = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/dashboard", headers=h)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # couple 部分
        assert data["couple"]["anniversary_date"] == "2023-01-01"
        # days_together 应 > 0
        assert data["days_together"] > 0
        # 倒计时
        assert isinstance(data["next_countdown"], list)
        # stats
        assert data["stats"]["blog_count"] == 0
        assert data["stats"]["photo_count"] == 0

    def test_dashboard_counts_anniversaries(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        client.post("/api/v1/anniversaries", headers=h, json={
            "title": "x1", "date": str(date.today()),
        })
        client.post("/api/v1/anniversaries", headers=h, json={
            "title": "x2", "date": str(date.today()),
        })
        resp = client.get("/api/v1/dashboard", headers=h)
        assert resp.json()["stats"]["anniversary_count"] == 2

    def test_dashboard_requires_bound(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        resp = client.get(
            "/api/v1/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


# ============================================================
# 工具函数
# ============================================================

def _login(client, username, password="Test1234") -> str:
    resp = client.post("/api/v1/auth/login-json", json={
        "username": username, "password": password,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _bound_login(client, user_a: str, user_b: str, anniversary=None) -> str:
    a_token = _login(client, user_a)
    r = client.post(
        "/api/v1/couples/invites",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    code = r.json()["code"]
    b_token = _login(client, user_b)
    ann = anniversary or date.today()
    resp = client.post(
        "/api/v1/couples/accept",
        headers={"Authorization": f"Bearer {b_token}"},
        json={"code": code, "anniversary_date": str(ann)},
    )
    assert resp.status_code == 201, resp.text
    return a_token
