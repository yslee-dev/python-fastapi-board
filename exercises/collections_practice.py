"""연습 문제 2: 컬렉션 (list, dict, set, tuple)

채점: uv run pytest exercises/test_collections_practice.py -v
특정 문제만: uv run pytest exercises/test_collections_practice.py -v -k problem1

게시글은 FastAPI 응답 JSON처럼 dict로 표현한다.

    post = {
        "id": 1,
        "title": "FastAPI 시작",
        "author": "kim",
        "tags": ["python", "fastapi"],
        "created_at": "2026-10-01",
    }

각 문제의 Java 코드는 '같은 일을 Java Stream으로 하면 이렇다'는 참고용이다.
Python에서는 for 문보다 컴프리헨션, 내장 함수(sorted, len, set 등)를 먼저 떠올려 보자.
모든 문제에서 입력 리스트(posts)를 직접 바꾸면 안 된다.
"""


def problem1_titles_of_author(posts: list[dict], author: str) -> list[str]:
    """문제 1. 특정 작성자의 글 제목만 원래 순서대로 모은다.

    Java:
        posts.stream()
             .filter(p -> p.get("author").equals(author))
             .map(p -> (String) p.get("title"))
             .toList();

    예: author="kim" → ["FastAPI 시작", "Pydantic 검증", "async 함정"]
    작성자가 없으면 빈 리스트.
    """
    return [post["title"] for post in posts if post.get("author") == author]


def problem2_count_by_author(posts: list[dict]) -> dict[str, int]:
    """문제 2. 작성자별 글 개수를 센다.

    Java:
        posts.stream()
             .collect(Collectors.groupingBy(p -> p.get("author"), Collectors.counting()));

    예: {"kim": 3, "lee": 1, "park": 1}
    """
    counts = {}
    for post in posts:
        author = post["author"]
        counts[author] = counts.get(author, 0) + 1
    return counts


def problem3_group_titles_by_author(posts: list[dict]) -> dict[str, list[str]]:
    """문제 3. 작성자별로 글 제목 목록을 묶는다. 제목은 원래 순서를 유지한다.

    Java:
        posts.stream()
             .collect(Collectors.groupingBy(
                 p -> p.get("author"),
                 Collectors.mapping(p -> p.get("title"), Collectors.toList())));

    예: {"kim": ["FastAPI 시작", "Pydantic 검증", "async 함정"],
         "lee": ["JPA 정리"],
         "park": ["Spring vs FastAPI"]}
    """
    titles_by_author = {}
    for post in posts:
        author = post["author"]
        if author not in titles_by_author:
            titles_by_author[author] = []
        titles_by_author[author].append(post["title"])
    return titles_by_author


def problem4_unique_tags(posts: list[dict]) -> list[str]:
    """문제 4. 모든 글의 태그를 중복 없이 모아 알파벳순으로 정렬한다.

    Java:
        posts.stream()
             .flatMap(p -> ((List<String>) p.get("tags")).stream())
             .distinct()
             .sorted()
             .toList();

    예: ["fastapi", "java", "jpa", "pydantic", "python"]
    태그가 빈 리스트인 글도 있다.
    """

    tags = []
    for post in posts:
        for tag in post["tags"]:
            tags.append(tag)
    return sorted(set(tags))


def problem5_latest_posts(posts: list[dict], n: int) -> list[int]:
    """문제 5. 최신 글 n개의 id를 돌려준다.

    정렬 기준: created_at 내림차순, created_at이 같으면 id 내림차순
    (이 프로젝트의 PostRepository.find_page와 같은 정렬이다)

    Java:
        posts.stream()
             .sorted(Comparator.comparing((Map<String, Object> p) -> (String) p.get("created_at"))
                               .thenComparing(p -> (Integer) p.get("id"))
                               .reversed())
             .limit(n)
             .map(p -> (Integer) p.get("id"))
             .toList();

    예: n=3 → [5, 4, 3]
    n이 글 개수보다 크면 전부 돌려준다.
    주의: 입력 리스트 posts의 순서가 바뀌면 안 된다.
    """
    raise NotImplementedError("여기를 채우세요")


def problem6_apply_patch(post: dict, patch: dict) -> dict:
    """문제 6 (보너스). PATCH 요청처럼 게시글의 일부 필드만 바꾼 '새' dict를 돌려준다.

    규칙
    - 바꿀 수 있는 필드는 "title", "content" 뿐이다. 다른 키(author, id 등)는 무시한다.
    - 원본 post는 바뀌면 안 된다.

    Java:
        Set<String> allowed = Set.of("title", "content");
        Map<String, Object> result = new HashMap<>(post);
        patch.forEach((k, v) -> { if (allowed.contains(k)) result.put(k, v); });
        return result;

    예: post={"id": 1, "title": "원래", "author": "kim"},
        patch={"title": "새 제목", "author": "hacker"}
        → {"id": 1, "title": "새 제목", "author": "kim"}
    """
    raise NotImplementedError("여기를 채우세요")
