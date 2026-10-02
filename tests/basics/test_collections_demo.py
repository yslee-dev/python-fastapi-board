from basics.collections_demo import first_and_rest, index_by_id, merge, paginate, squares_of_even


def test_squares_of_even():
    assert squares_of_even([1, 2, 3, 4]) == [4, 16]


def test_index_by_id():
    posts = [{"id": 1, "title": "a"}, {"id": 2, "title": "b"}]
    assert index_by_id(posts) == {1: {"id": 1, "title": "a"}, 2: {"id": 2, "title": "b"}}


def test_paginate_uses_slicing():
    items = list(range(1, 11))
    assert paginate(items, page=1, size=3) == [1, 2, 3]
    assert paginate(items, page=4, size=3) == [10]
    assert paginate(items, page=5, size=3) == []


def test_first_and_rest_unpacking():
    assert first_and_rest([1, 2, 3]) == (1, [2, 3])


def test_merge_later_values_win():
    base = {"title": "원래 제목", "content": "원래 내용"}
    assert merge(base, {"title": "새 제목"}) == {"title": "새 제목", "content": "원래 내용"}
    assert base["title"] == "원래 제목"  # 원본은 바뀌지 않는다
