import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://board:board@localhost:5433/board_test"
)
test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def client() -> Iterator[TestClient]:
    # 04단계의 단순한 방식: 테스트마다 테이블을 만들고 지운다 (06단계에서 개선)
    Base.metadata.create_all(test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # get_db 대신 테스트 DB 세션을 주입한다 (@MockBean / @TestConfiguration 역할)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(test_engine)


def create_post(client: TestClient, **overrides: str) -> dict:
    payload = {"title": "제목", "content": "내용", "author": "홍길동"} | overrides
    response = client.post("/posts", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# --- 생성 ---


def test_create_post(client):
    response = client.post("/posts", json={"title": "첫 글", "content": "안녕", "author": "홍길동"})

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == "첫 글"
    assert body["content"] == "안녕"
    assert body["author"] == "홍길동"
    assert body["created_at"]
    assert body["updated_at"]


def test_create_post_rejects_too_long_title(client):
    response = client.post("/posts", json={"title": "a" * 101, "content": "c", "author": "a"})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "title"]
    assert error["type"] == "string_too_long"


def test_create_post_rejects_blank_title(client):
    response = client.post("/posts", json={"title": "   ", "content": "c", "author": "a"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]


def test_create_post_requires_author(client):
    response = client.post("/posts", json={"title": "t", "content": "c"})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "author"]
    assert error["type"] == "missing"


# --- 조회 ---


def test_get_post(client):
    created = create_post(client)

    response = client.get(f"/posts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_post_not_found(client):
    response = client.get("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}


def test_get_post_with_non_integer_id(client):
    response = client.get("/posts/abc")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "post_id"]


# --- 목록 ---


def test_list_posts_newest_first_with_pagination(client):
    for title in ["1", "2", "3"]:
        create_post(client, title=title)

    first_page = client.get("/posts", params={"page": 1, "size": 2}).json()
    second_page = client.get("/posts", params={"page": 2, "size": 2}).json()

    assert [p["title"] for p in first_page["items"]] == ["3", "2"]
    assert first_page["total"] == 3
    assert first_page["page"] == 1
    assert first_page["size"] == 2
    assert [p["title"] for p in second_page["items"]] == ["1"]


def test_list_posts_uses_default_paging(client):
    body = client.get("/posts").json()

    assert body == {"items": [], "total": 0, "page": 1, "size": 10}


def test_list_posts_page_beyond_last_returns_empty_items(client):
    create_post(client)

    body = client.get("/posts", params={"page": 5}).json()

    assert body["items"] == []
    assert body["total"] == 1


@pytest.mark.parametrize("params", [{"page": 0}, {"size": 0}, {"size": 101}])
def test_list_posts_rejects_invalid_paging(client, params):
    response = client.get("/posts", params=params)

    assert response.status_code == 422


# --- 수정 ---


def test_update_post_partially(client):
    created = create_post(client, title="원래 제목", content="원래 내용")

    response = client.patch(f"/posts/{created['id']}", json={"title": "새 제목"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "새 제목"
    assert body["content"] == "원래 내용"  # 보내지 않은 필드는 유지
    assert body["author"] == "홍길동"


def test_update_post_rejects_explicit_null(client):
    created = create_post(client)

    response = client.patch(f"/posts/{created['id']}", json={"title": None})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]


def test_update_post_ignores_author(client):
    created = create_post(client, author="홍길동")

    response = client.patch(f"/posts/{created['id']}", json={"author": "임꺽정"})

    assert response.status_code == 200
    assert response.json()["author"] == "홍길동"


def test_update_post_not_found(client):
    response = client.patch("/posts/999", json={"title": "새 제목"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}


# --- 삭제 ---


def test_delete_post(client):
    created = create_post(client)

    response = client.delete(f"/posts/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/posts/{created['id']}").status_code == 404


def test_delete_post_not_found(client):
    response = client.delete("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}
