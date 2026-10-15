"""
M-13 集成测试：Blog 改造 + couple 维度缓存

覆盖：
- 已绑定用户创建博客 → 自动注入 couple_id
- 未绑定用户创建博客 → couple_id = None（v1 兼容）
- 列表（已绑定）→ 返回「我 + 伴侣」的所有博客
- 列表（未绑定）→ 返回「我」的所有博客（v1 行为）
- 详情：作者可见 / 伴侣可见 / 第三方 404
- 缓存失效：blog 写后清 couple 维度 timeline/dashboard 缓存
- v1 老数据（couple_id=None）读 v2 接口不破
"""
import time
import pytest


def _create_blog(client, headers, **overrides):
    payload = {
        "title": "Hello",
        "content": "Body",
        "tags": [],
        "is_public": False,
    }
    payload.update(overrides)
    r = client.post("/api/v1/blogs/", headers=headers, json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def _login(client, username, password="Test1234") -> str:
    r = client.post("/api/v1/auth/login-json", json={
        "username": username, "password": password,
    })
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _bind_pair(client, user_a_name, user_b_name, anniversary="2024-01-01"):
    """完整走一遍绑定流程"""
    a_token = _login(client, user_a_name)
    r = client.post(
        "/api/v1/couples/invites",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    code = r.json()["code"]
    b_token = _login(client, user_b_name)
    resp = client.post(
        "/api/v1/couples/accept",
        headers={"Authorization": f"Bearer {b_token}"},
        json={"code": code, "anniversary_date": anniversary},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _fresh_token(client, username, password="Test1234"):
    """给已存在用户重新拿 token（绕过缓存的旧 token）"""
    return _login(client, username, password)


# ============================================================
# 创建博客：自动注入 couple_id
# ============================================================

class TestCreateBlogCoupleId:

    def test_create_unbound_user_couple_id_is_null(self, client, make_user):
        """v1 兼容：未绑定用户创建博客 → couple_id = null"""
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        b = _create_blog(client, h, title="solo post")
        assert b["couple_id"] is None
        assert b["event_date"] is None

    def test_create_bound_user_couple_id_is_set(self, client, make_user):
        """v2：已绑定用户创建博客 → couple_id 自动注入"""
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        bind_data = _bind_pair(client, "alice", "bob", "2024-01-01")
        couple_id = bind_data["couple"]["id"]
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        b = _create_blog(client, h, title="couple post")
        assert b["couple_id"] == couple_id

    def test_create_bound_partner_couple_id_is_same(self, client, make_user):
        """伴侣创建博客的 couple_id 与发起方相同"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        bind_data = _bind_pair(client, "alice", "bob", "2024-01-01")
        couple_id = bind_data["couple"]["id"]
        token = _login(client, "bob")
        h = {"Authorization": f"Bearer {token}"}
        b = _create_blog(client, h, title="bob post")
        assert b["couple_id"] == couple_id


# ============================================================
# 列表：双维度
# ============================================================

class TestListBlogsCouple:

    def test_list_unbound_returns_only_own(self, client, make_user):
        """v1 行为：未绑定用户列表只返回自己的"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        a_token = _login(client, "alice")
        b_token = _login(client, "bob")
        a_h = {"Authorization": f"Bearer {a_token}"}
        b_h = {"Authorization": f"Bearer {b_token}"}
        _create_blog(client, a_h, title="alice post")
        _create_blog(client, b_h, title="bob post")
        r1 = client.get("/api/v1/blogs/", headers=a_h).json()
        assert r1["total"] == 1
        assert r1["items"][0]["title"] == "alice post"

    def test_list_bound_returns_both(self, client, make_user):
        """v2 行为：已绑定用户列表返回自己 + 伴侣"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-01-01")
        a_token = _login(client, "alice")
        b_token = _login(client, "bob")
        a_h = {"Authorization": f"Bearer {a_token}"}
        b_h = {"Authorization": f"Bearer {b_token}"}
        _create_blog(client, a_h, title="alice post")
        _create_blog(client, b_h, title="bob post")
        r = client.get("/api/v1/blogs/", headers=a_h).json()
        titles = sorted(i["title"] for i in r["items"])
        assert titles == ["alice post", "bob post"]
        assert r["total"] == 2

    def test_list_bound_isolated_from_other_couple(self, client, make_user):
        """绑定后不能看到其他 couple 的博客"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        make_user(username="carol", email="c@x.com")
        make_user(username="dave", email="d@x.com")
        _bind_pair(client, "alice", "bob", "2024-01-01")
        _bind_pair(client, "carol", "dave", "2024-02-01")
        a_token = _login(client, "alice")
        c_token = _login(client, "carol")
        a_h = {"Authorization": f"Bearer {a_token}"}
        c_h = {"Authorization": f"Bearer {c_token}"}
        _create_blog(client, a_h, title="alice post")
        _create_blog(client, c_h, title="carol post")
        r = client.get("/api/v1/blogs/", headers=a_h).json()
        titles = [i["title"] for i in r["items"]]
        assert "alice post" in titles
        assert "carol post" not in titles


# ============================================================
# 详情：作者 OR couple 可见
# ============================================================

class TestGetBlogCouple:

    def test_author_can_read_own(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        b = _create_blog(client, h, title="mine")
        r = client.get(f"/api/v1/blogs/{b['id']}", headers=h)
        assert r.status_code == 200
        assert r.json()["title"] == "mine"

    def test_partner_can_read(self, client, make_user):
        """v2：伴侣能读到我的博客（couple 维度）"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-01-01")
        a_token = _login(client, "alice")
        b_token = _login(client, "bob")
        a_h = {"Authorization": f"Bearer {a_token}"}
        b_h = {"Authorization": f"Bearer {b_token}"}
        b = _create_blog(client, a_h, title="alice post")
        r = client.get(f"/api/v1/blogs/{b['id']}", headers=b_h)
        assert r.status_code == 200
        assert r.json()["title"] == "alice post"

    def test_outsider_404(self, client, make_user):
        """v2：无关用户仍 404"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        make_user(username="carol", email="c@x.com")
        a_token = _login(client, "alice")
        c_token = _login(client, "carol")
        a_h = {"Authorization": f"Bearer {a_token}"}
        c_h = {"Authorization": f"Bearer {c_token}"}
        b = _create_blog(client, a_h, title="alice post")
        r = client.get(f"/api/v1/blogs/{b['id']}", headers=c_h)
        assert r.status_code == 404

    def test_partner_can_update(self, client, make_user):
        """v2：伴侣能改我的博客（couple 维度）"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-01-01")
        a_token = _login(client, "alice")
        b_token = _login(client, "bob")
        a_h = {"Authorization": f"Bearer {a_token}"}
        b_h = {"Authorization": f"Bearer {b_token}"}
        b = _create_blog(client, a_h, title="alice")
        r = client.put(
            f"/api/v1/blogs/{b['id']}", headers=b_h,
            json={"title": "renamed by bob"},
        )
        assert r.status_code == 200
        assert r.json()["title"] == "renamed by bob"

    def test_partner_can_delete(self, client, make_user):
        """v2：伴侣能删我的博客（couple 维度）"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-01-01")
        a_token = _login(client, "alice")
        b_token = _login(client, "bob")
        a_h = {"Authorization": f"Bearer {a_token}"}
        b_h = {"Authorization": f"Bearer {b_token}"}
        b = _create_blog(client, a_h, title="alice")
        r = client.delete(f"/api/v1/blogs/{b['id']}", headers=b_h)
        assert r.status_code == 204


# ============================================================
# 缓存一致性
# ============================================================

class TestCacheInvalidation:

    def test_create_invalidates_dashboard_cache(self, client, make_user):
        """创建博客后，dashboard 缓存应被清掉"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-01-01")
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        # 1. 触发 dashboard 缓存
        r1 = client.get("/api/v1/dashboard", headers=h)
        assert r1.status_code == 200
        d1 = r1.json()
        # 2. 直接看 Redis，确认 dashboard 缓存键存在
        from app.core.redis_client import get_redis
        r = get_redis()
        keys_before = list(r.scan_iter("cache:dashboard:couple:*"))
        assert len(keys_before) >= 1
        # 3. 创建博客（应触发 cache invalidation）
        _create_blog(client, h, title="new post")
        # 4. dashboard 缓存键应被清空
        keys_after = list(r.scan_iter("cache:dashboard:couple:*"))
        assert len(keys_after) == 0

    def test_create_invalidates_timeline_cache(self, client, make_user):
        """创建博客后，timeline 缓存应被清掉"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-01-01")
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        client.get("/api/v1/timeline", headers=h)
        from app.core.redis_client import get_redis
        r = get_redis()
        keys_before = list(r.scan_iter("cache:timeline:couple:*"))
        assert len(keys_before) >= 1
        _create_blog(client, h, title="new")
        keys_after = list(r.scan_iter("cache:timeline:couple:*"))
        assert len(keys_after) == 0

    def test_update_invalidates_blog_list_cache(self, client, make_user):
        """更新博客后，blog 列表缓存应被清掉（couple 维度）"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-01-01")
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        b = _create_blog(client, h, title="old")
        # 触发缓存
        client.get("/api/v1/blogs/", headers=h)
        from app.core.redis_client import get_redis
        r = get_redis()
        keys_before = list(r.scan_iter("cache:blog:list:couple:*"))
        assert len(keys_before) >= 1
        # 更新
        client.put(
            f"/api/v1/blogs/{b['id']}", headers=h,
            json={"title": "new"},
        )
        keys_after = list(r.scan_iter("cache:blog:list:couple:*"))
        assert len(keys_after) == 0


# ============================================================
# 写操作走 couple 缓存失效（anniversary/album/photo 写后清 dashboard）
# ============================================================

class TestCrossModuleCacheInvalidation:

    def test_anniversary_create_invalidates_dashboard(self, client, make_user):
        """创建纪念日后 dashboard 缓存被清"""
        from datetime import date, timedelta
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-01-01")
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        client.get("/api/v1/dashboard", headers=h)
        from app.core.redis_client import get_redis
        r = get_redis()
        keys_before = list(r.scan_iter("cache:dashboard:couple:*"))
        assert len(keys_before) >= 1
        # 创建纪念日
        ann_date = (date.today() - timedelta(days=100)).isoformat()
        client.post(
            "/api/v1/anniversaries", headers=h,
            json={
                "title": "100 days", "date": ann_date,
                "type": "ONCE", "is_recurring": False,
            },
        )
        keys_after = list(r.scan_iter("cache:dashboard:couple:*"))
        assert len(keys_after) == 0

    def test_album_create_invalidates_dashboard(self, client, make_user):
        """创建相册后 dashboard 缓存被清"""
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-01-01")
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        client.get("/api/v1/dashboard", headers=h)
        from app.core.redis_client import get_redis
        r = get_redis()
        keys_before = list(r.scan_iter("cache:dashboard:couple:*"))
        assert len(keys_before) >= 1
        client.post(
            "/api/v1/albums", headers=h,
            json={"name": "Trip 2025", "description": ""},
        )
        keys_after = list(r.scan_iter("cache:dashboard:couple:*"))
        assert len(keys_after) == 0


# ============================================================
# 写操作走 couple 缓存失效（couple accept 后清 dashboard）
# ============================================================

class TestCoupleBindCacheInvalidation:

    def test_accept_invite_invalidates_user_blog_cache(self, client, make_user):
        """接受邀请后双方 author 维度缓存应被清"""
        alice = make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        a_token = _login(client, "alice")
        a_h = {"Authorization": f"Bearer {a_token}"}
        # alice 在未绑定时发博客 + 触发 list 缓存
        _create_blog(client, a_h, title="pre-bind")
        client.get("/api/v1/blogs/", headers=a_h)
        from app.core.redis_client import get_redis
        r = get_redis()
        keys_before = list(r.scan_iter(f"cache:blog:list:{alice.id}:*"))
        assert len(keys_before) >= 1
        # 接受邀请
        r_inv = client.post(
            "/api/v1/couples/invites", headers=a_h,
        )
        code = r_inv.json()["code"]
        b_token = _login(client, "bob")
        client.post(
            "/api/v1/couples/accept",
            headers={"Authorization": f"Bearer {b_token}"},
            json={"code": code, "anniversary_date": "2024-01-01"},
        )
        # 绑定后 alice 的 author 维度缓存应被清
        keys_after = list(r.scan_iter(f"cache:blog:list:{alice.id}:*"))
        assert len(keys_after) == 0


# ============================================================
# v1 兼容
# ============================================================

class TestV1BackwardsCompat:

    def test_old_unbound_list_path_still_works(self, client, make_user):
        """v1 老用户（未绑定）创建并查看博客完全正常"""
        make_user(username="solo", email="s@x.com")
        token = _login(client, "solo")
        h = {"Authorization": f"Bearer {token}"}
        _create_blog(client, h, title="A")
        _create_blog(client, h, title="B")
        r = client.get("/api/v1/blogs/", headers=h).json()
        assert r["total"] == 2
        for item in r["items"]:
            assert item["couple_id"] is None
            assert item["event_date"] is None
            assert item["author_id"] > 0

    def test_old_unbound_update_delete_still_works(self, client, make_user):
        """v1 老用户（未绑定）update/delete 仍按 author_id 校验"""
        make_user(username="solo", email="s@x.com")
        token = _login(client, "solo")
        h = {"Authorization": f"Bearer {token}"}
        b = _create_blog(client, h, title="old")
        r = client.put(
            f"/api/v1/blogs/{b['id']}", headers=h,
            json={"title": "new"},
        )
        assert r.status_code == 200
        assert r.json()["title"] == "new"
        d = client.delete(f"/api/v1/blogs/{b['id']}", headers=h)
        assert d.status_code == 204
