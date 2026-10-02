import pytest
from httpx import AsyncClient


async def create_post(client: AsyncClient, **overrides: str) -> dict:
    payload = {"title": "제목", "content": "내용", "author": "홍길동"} | overrides
    response = await client.post("/posts", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# --- 생성 ---


async def test_create_post(client):
    response = await client.post(
        "/posts", json={"title": "첫 글", "content": "안녕", "author": "홍길동"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == "첫 글"
    assert body["content"] == "안녕"
    assert body["author"] == "홍길동"
    assert body["created_at"]
    assert body["updated_at"]


async def test_create_post_rejects_too_long_title(client):
    response = await client.post("/posts", json={"title": "a" * 101, "content": "c", "author": "a"})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "title"]
    assert error["type"] == "string_too_long"


async def test_create_post_rejects_blank_title(client):
    response = await client.post("/posts", json={"title": "   ", "content": "c", "author": "a"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]


async def test_create_post_requires_author(client):
    response = await client.post("/posts", json={"title": "t", "content": "c"})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "author"]
    assert error["type"] == "missing"


# --- 조회 ---


async def test_get_post(client):
    created = await create_post(client)

    response = await client.get(f"/posts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


async def test_get_post_not_found(client):
    response = await client.get("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}


async def test_get_post_with_non_integer_id(client):
    response = await client.get("/posts/abc")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "post_id"]


# --- 목록 ---


async def test_list_posts_newest_first_with_pagination(client):
    for title in ["1", "2", "3"]:
        await create_post(client, title=title)

    first_page = (await client.get("/posts", params={"page": 1, "size": 2})).json()
    second_page = (await client.get("/posts", params={"page": 2, "size": 2})).json()

    assert [p["title"] for p in first_page["items"]] == ["3", "2"]
    assert first_page["total"] == 3
    assert first_page["page"] == 1
    assert first_page["size"] == 2
    assert [p["title"] for p in second_page["items"]] == ["1"]


async def test_list_posts_uses_default_paging(client):
    body = (await client.get("/posts")).json()

    assert body == {"items": [], "total": 0, "page": 1, "size": 10}


async def test_list_posts_page_beyond_last_returns_empty_items(client):
    await create_post(client)

    body = (await client.get("/posts", params={"page": 5})).json()

    assert body["items"] == []
    assert body["total"] == 1


@pytest.mark.parametrize("params", [{"page": 0}, {"size": 0}, {"size": 101}])
async def test_list_posts_rejects_invalid_paging(client, params):
    response = await client.get("/posts", params=params)

    assert response.status_code == 422


# --- 수정 ---


async def test_update_post_partially(client):
    created = await create_post(client, title="원래 제목", content="원래 내용")

    response = await client.patch(f"/posts/{created['id']}", json={"title": "새 제목"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "새 제목"
    assert body["content"] == "원래 내용"  # 보내지 않은 필드는 유지
    assert body["author"] == "홍길동"


async def test_update_post_rejects_explicit_null(client):
    created = await create_post(client)

    response = await client.patch(f"/posts/{created['id']}", json={"title": None})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]


async def test_update_post_ignores_author(client):
    created = await create_post(client, author="홍길동")

    response = await client.patch(f"/posts/{created['id']}", json={"author": "임꺽정"})

    assert response.status_code == 200
    assert response.json()["author"] == "홍길동"


async def test_update_post_not_found(client):
    response = await client.patch("/posts/999", json={"title": "새 제목"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}


# --- 삭제 ---


async def test_delete_post(client):
    created = await create_post(client)

    response = await client.delete(f"/posts/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert (await client.get(f"/posts/{created['id']}")).status_code == 404


async def test_delete_post_not_found(client):
    response = await client.delete("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}


# --- 로깅 ---


async def test_create_post_writes_info_log(client, caplog):
    with caplog.at_level("INFO", logger="app.posts.service"):
        created = await create_post(client)

    assert f"게시글 생성 id={created['id']}" in caplog.text
