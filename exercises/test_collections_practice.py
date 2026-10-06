import copy

import pytest

from exercises.collections_practice import (
    problem1_titles_of_author,
    problem2_count_by_author,
    problem3_group_titles_by_author,
    problem4_unique_tags,
    problem5_latest_posts,
    problem6_apply_patch,
)


@pytest.fixture
def posts() -> list[dict]:
    return [
        {
            "id": 1,
            "title": "FastAPI 시작",
            "author": "kim",
            "tags": ["python", "fastapi"],
            "created_at": "2026-10-01",
        },
        {
            "id": 2,
            "title": "JPA 정리",
            "author": "lee",
            "tags": ["java", "jpa"],
            "created_at": "2026-10-02",
        },
        {
            "id": 3,
            "title": "Pydantic 검증",
            "author": "kim",
            "tags": ["python", "pydantic"],
            "created_at": "2026-10-02",
        },
        {
            "id": 4,
            "title": "Spring vs FastAPI",
            "author": "park",
            "tags": ["java", "python"],
            "created_at": "2026-10-03",
        },
        {
            "id": 5,
            "title": "async 함정",
            "author": "kim",
            "tags": [],
            "created_at": "2026-10-03",
        },
    ]


# --- 문제 1 ---


def test_problem1_titles_of_author(posts):
    assert problem1_titles_of_author(posts, "kim") == [
        "FastAPI 시작",
        "Pydantic 검증",
        "async 함정",
    ]


def test_problem1_unknown_author_returns_empty_list(posts):
    assert problem1_titles_of_author(posts, "nobody") == []


def test_problem1_empty_posts():
    assert problem1_titles_of_author([], "kim") == []


# --- 문제 2 ---


def test_problem2_count_by_author(posts):
    assert problem2_count_by_author(posts) == {"kim": 3, "lee": 1, "park": 1}


def test_problem2_empty_posts():
    assert problem2_count_by_author([]) == {}


# --- 문제 3 ---


def test_problem3_group_titles_by_author(posts):
    assert problem3_group_titles_by_author(posts) == {
        "kim": ["FastAPI 시작", "Pydantic 검증", "async 함정"],
        "lee": ["JPA 정리"],
        "park": ["Spring vs FastAPI"],
    }


def test_problem3_empty_posts():
    assert problem3_group_titles_by_author([]) == {}


# --- 문제 4 ---


def test_problem4_unique_tags_sorted(posts):
    assert problem4_unique_tags(posts) == ["fastapi", "java", "jpa", "pydantic", "python"]


def test_problem4_returns_list_not_set(posts):
    assert isinstance(problem4_unique_tags(posts), list)


def test_problem4_no_tags():
    assert problem4_unique_tags([{"tags": []}, {"tags": []}]) == []


# --- 문제 5 ---


def test_problem5_latest_posts(posts):
    assert problem5_latest_posts(posts, 3) == [5, 4, 3]


def test_problem5_n_larger_than_posts(posts):
    assert problem5_latest_posts(posts, 100) == [5, 4, 3, 2, 1]


def test_problem5_zero(posts):
    assert problem5_latest_posts(posts, 0) == []


def test_problem5_does_not_reorder_input(posts):
    original_ids = [p["id"] for p in posts]

    problem5_latest_posts(posts, 3)

    assert [p["id"] for p in posts] == original_ids


# --- 문제 6 (보너스) ---


def test_problem6_applies_allowed_fields_only():
    post = {"id": 1, "title": "원래", "content": "본문", "author": "kim"}

    result = problem6_apply_patch(post, {"title": "새 제목", "author": "hacker", "id": 999})

    assert result == {"id": 1, "title": "새 제목", "content": "본문", "author": "kim"}


def test_problem6_does_not_modify_original():
    post = {"id": 1, "title": "원래", "content": "본문", "author": "kim"}
    snapshot = copy.deepcopy(post)

    problem6_apply_patch(post, {"title": "새 제목"})

    assert post == snapshot


def test_problem6_empty_patch_returns_equal_copy():
    post = {"id": 1, "title": "원래", "content": "본문", "author": "kim"}

    result = problem6_apply_patch(post, {})

    assert result == post
    assert result is not post  # 같은 내용의 '새' dict여야 한다
