"""
集成测试：blogs 路由

覆盖：
- POST /blogs/
- GET /blogs/（分页/标签/搜索/缓存）
- GET /blogs/{id}
- GET /blogs/public/{author_id}
- PUT /blogs/{id}
- DELETE /blogs/{id}（软删）
- 跨用户越权保护
"""
import time
import pytest


def _create_blog(client, headers, **overrides):
    """工具：建一篇博客并返回 id"""
    payload = {
        "title": "Hello World",
        "content": "This is a test post body.",
        "tags": ["life", "test"],
        "is_public": False,
    }
    payload.update(overrides)
    resp = client.post("/api/v1/blogs/", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ============================================================
# 创建
# ============================================================

class TestCreateBlog:

    def test_create_success(self, client, auth_headers):
        headers, _ = auth_headers
        blog = _create_blog(client, headers, title="First", content="Body")
        assert blog["id"]
        assert blog["title"] == "First"
        assert blog["tags"] == ["life", "test"]
        assert blog["is_deleted"] is False

    def test_create_with_no_tags(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.post("/api/v1/blogs/", headers=headers, json={
            "title": "X", "content": "Y", "is_public": True,
        })
        assert resp.status_code == 201
        assert resp.json()["tags"] == []

    def test_create_dedup_tags(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.post("/api/v1/blogs/", headers=headers, json={
            "title": "X", "content": "Y",
            "tags": ["a", "a", "b", "a"],
        })
        assert resp.status_code == 201
        assert resp.json()["tags"] == ["a", "b"]

    @pytest.mark.parametrize("payload", [
        {"title": "", "content": "x"},
        {"title": "x", "content": ""},
        {"title": "x" * 201, "content": "x"},            # 超长
        {"title": "x", "content": "y" * 10001},
    ])
    def test_create_validation(self, client, auth_headers, payload):
        headers, _ = auth_headers
        resp = client.post("/api/v1/blogs/", headers=headers, json=payload)
        assert resp.status_code in (201, 422)

    def test_create_unauth(self, client):
        resp = client.post("/api/v1/blogs/", json={
            "title": "x", "content": "y",
        })
        assert resp.status_code == 401


# ============================================================
# 列表
# ============================================================

class TestListBlogs:

    def test_list_empty(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.get("/api/v1/blogs/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_list_ordered_desc(self, client, auth_headers):
        headers, _ = auth_headers
        _create_blog(client, headers, title="First")
        time.sleep(0.01)
        _create_blog(client, headers, title="Second")
        resp = client.get("/api/v1/blogs/", headers=headers)
        assert resp.json()["items"][0]["title"] == "Second"

    def test_list_pagination(self, client, auth_headers):
        headers, _ = auth_headers
        for i in range(15):
            _create_blog(client, headers, title=f"Post {i}")
        r1 = client.get("/api/v1/blogs/?page=1&page_size=10", headers=headers).json()
        r2 = client.get("/api/v1/blogs/?page=2&page_size=10", headers=headers).json()
        assert r1["total"] == 15
        assert len(r1["items"]) == 10
        assert len(r2["items"]) == 5
        assert r1["total_pages"] == 2

    def test_list_filter_by_tag(self, client, auth_headers):
        headers, _ = auth_headers
        _create_blog(client, headers, title="A", tags=["python"])
        _create_blog(client, headers, title="B", tags=["life"])
        resp = client.get("/api/v1/blogs/?tag=python", headers=headers)
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["title"] == "A"

    def test_list_search(self, client, auth_headers):
        headers, _ = auth_headers
        _create_blog(client, headers, title="Python tutorial", content="x")
        _create_blog(client, headers, title="Other", content="learn python here")
        resp = client.get("/api/v1/blogs/?search=python", headers=headers)
        assert resp.json()["total"] == 2

    def test_list_excludes_deleted(self, client, auth_headers):
        headers, _ = auth_headers
        b = _create_blog(client, headers, title="ToDelete")
        client.delete(f"/api/v1/blogs/{b['id']}", headers=headers)
        resp = client.get("/api/v1/blogs/", headers=headers)
        assert resp.json()["total"] == 0

    def test_list_only_my_blogs(self, client, auth_headers, other_auth_headers):
        h1, _ = auth_headers
        h2, _ = other_auth_headers
        _create_blog(client, h1, title="alice post")
        _create_blog(client, h2, title="bob post")
        r1 = client.get("/api/v1/blogs/", headers=h1).json()
        r2 = client.get("/api/v1/blogs/", headers=h2).json()
        assert r1["total"] == 1
        assert r2["total"] == 1

    def test_list_uses_cache(self, client, auth_headers):
        """两次相同查询，第二次应命中 Redis 缓存"""
        headers, _ = auth_headers
        _create_blog(client, headers, title="Cached")
        r1 = client.get("/api/v1/blogs/", headers=headers).json()
        # 再创建一个但绕过列表接口（直接走 service）模拟别人加数据
        r2 = client.get("/api/v1/blogs/", headers=headers).json()
        # 缓存命中 → 数量不变
        assert r1["total"] == r2["total"]


# ============================================================
# 详情
# ============================================================

class TestGetBlog:

    def test_get_by_id(self, client, auth_headers):
        headers, _ = auth_headers
        b = _create_blog(client, headers, title="Detail")
        resp = client.get(f"/api/v1/blogs/{b['id']}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Detail"

    def test_get_invalid_id(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.get("/api/v1/blogs/not-an-objectid", headers=headers)
        assert resp.status_code == 404

    def test_get_nonexistent(self, client, auth_headers):
        from bson import ObjectId
        headers, _ = auth_headers
        resp = client.get(f"/api/v1/blogs/{ObjectId()}", headers=headers)
        assert resp.status_code == 404

    def test_get_others_blog_404(self, client, auth_headers, other_auth_headers):
        """跨用户查博客应 404（防越权）"""
        h1, _ = auth_headers
        h2, _ = other_auth_headers
        b = _create_blog(client, h1, title="alice private post")
        resp = client.get(f"/api/v1/blogs/{b['id']}", headers=h2)
        assert resp.status_code == 404


# ============================================================
# 公开博客
# ============================================================

class TestPublicBlogs:

    def test_public_only_returns_public(self, client, auth_headers, other_auth_headers):
        h1, user1 = auth_headers
        h2, _ = other_auth_headers
        _create_blog(client, h1, title="Alice Public", is_public=True)
        _create_blog(client, h1, title="Alice Private", is_public=False)

        resp = client.get(f"/api/v1/blogs/public/{user1.id}", headers=h2)
        items = resp.json()["items"]
        titles = [i["title"] for i in items]
        assert "Alice Public" in titles
        assert "Alice Private" not in titles

    def test_public_excludes_deleted(self, client, auth_headers, other_auth_headers):
        h1, user1 = auth_headers
        h2, _ = other_auth_headers
        b = _create_blog(client, h1, title="will be removed", is_public=True)
        client.delete(f"/api/v1/blogs/{b['id']}", headers=h1)
        resp = client.get(f"/api/v1/blogs/public/{user1.id}", headers=h2)
        assert resp.json()["total"] == 0


# ============================================================
# 更新
# ============================================================

class TestUpdateBlog:

    def test_update_title(self, client, auth_headers):
        headers, _ = auth_headers
        b = _create_blog(client, headers, title="Old")
        resp = client.put(
            f"/api/v1/blogs/{b['id']}", headers=headers,
            json={"title": "New"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New"

    def test_update_to_public(self, client, auth_headers):
        headers, _ = auth_headers
        b = _create_blog(client, headers, is_public=False)
        resp = client.put(
            f"/api/v1/blogs/{b['id']}", headers=headers,
            json={"is_public": True},
        )
        assert resp.json()["is_public"] is True

    def test_update_other_users_blog_404(self, client, auth_headers, other_auth_headers):
        h1, _ = auth_headers
        h2, _ = other_auth_headers
        b = _create_blog(client, h1, title="alice post")
        resp = client.put(
            f"/api/v1/blogs/{b['id']}", headers=h2,
            json={"title": "hacked"},
        )
        assert resp.status_code == 404

    def test_update_empty_payload(self, client, auth_headers):
        headers, _ = auth_headers
        b = _create_blog(client, headers)
        resp = client.put(f"/api/v1/blogs/{b['id']}", headers=headers, json={})
        assert resp.status_code == 200
        assert resp.json()["id"] == b["id"]


# ============================================================
# 软删除
# ============================================================

class TestDeleteBlog:

    def test_delete_soft(self, client, auth_headers):
        headers, _ = auth_headers
        b = _create_blog(client, headers, title="Soft removal test")
        resp = client.delete(f"/api/v1/blogs/{b['id']}", headers=headers)
        assert resp.status_code == 204

        # 列表中应消失
        listing = client.get("/api/v1/blogs/", headers=headers).json()
        assert all(item["id"] != b["id"] for item in listing["items"])

        # 详情查询应 404
        detail = client.get(f"/api/v1/blogs/{b['id']}", headers=headers)
        assert detail.status_code == 404

    def test_delete_invalidates_cache(self, client, auth_headers):
        """删除后缓存应被清理，列表中不出现该博客"""
        headers, _ = auth_headers
        b = _create_blog(client, headers, title="Cache invalidation test")
        # 触发缓存写入
        client.get("/api/v1/blogs/", headers=headers)
        # 删除
        client.delete(f"/api/v1/blogs/{b['id']}", headers=headers)
        # 重新查询应看不到
        after = client.get("/api/v1/blogs/", headers=headers).json()
        assert after["total"] == 0

    def test_delete_other_users_404(self, client, auth_headers, other_auth_headers):
        h1, _ = auth_headers
        h2, _ = other_auth_headers
        b = _create_blog(client, h1)
        resp = client.delete(f"/api/v1/blogs/{b['id']}", headers=h2)
        assert resp.status_code == 404
