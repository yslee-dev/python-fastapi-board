# 04. PostgreSQL + SQLAlchemy + Alembic

```bash
git diff step-03 step-04 -- app/ tests/
docker compose up -d --wait && uv run alembic upgrade head
```

저장소를 `dict`에서 PostgreSQL로 바꿨다. **스키마와 API 계약, 테스트 본문은 그대로**이고,
바뀐 것은 "데이터를 어디에 두느냐"뿐이다. `git diff step-03 step-04 -- tests/`를 보면 테스트는 픽스처만 바뀌었다.

## 이번에 바뀐 것

**세 가지 객체의 관계**

```
engine (커넥션 풀, 앱 전체에 하나)
  └─ SessionLocal (세션 공장)
       └─ Session (요청 하나당 하나, 영속성 컨텍스트)
```

| 코드 | 하는 일 |
|---|---|
| `create_engine(URL)` | 커넥션 풀을 만든다. 실제 연결은 처음 쓸 때 맺는다 |
| `sessionmaker(...)` | 세션을 만드는 공장. `SessionLocal()`을 부를 때마다 새 세션 |
| `get_db()` | 요청마다 세션을 열어 `yield`로 넘기고, 응답 후 `finally`에서 닫는다 |
| `class Post(Base)` | 테이블 매핑. `Mapped[str]` → NOT NULL, `Mapped[str \| None]`이면 NULL 허용 |
| `db.get(Post, id)` | PK로 조회. 없으면 `None` |
| `select(Post).order_by(...).offset().limit()` | SQLAlchemy 2.0 스타일 쿼리 빌더 |
| `db.scalars(stmt).all()` | 쿼리 실행 → `Post` 객체 리스트 |
| `db.add` / `db.commit` / `db.refresh` / `db.delete` | 저장 / 커밋 / DB 값 다시 읽기 / 삭제 |
| `DbSession = Annotated[Session, Depends(get_db)]` | "이 인자는 `get_db()`가 만들어 준다"는 선언을 재사용하는 별칭 |
| `ConfigDict(from_attributes=True)` | `PostResponse`가 dict뿐 아니라 ORM 객체(`post.title`)에서도 값을 읽게 한다 |

**Alembic**

- `alembic/env.py`가 앱의 `Base.metadata`(모델 정의)와 DB URL을 가져온다.
- `alembic revision --autogenerate`는 **모델과 실제 DB를 비교해서** 마이그레이션 파일을 만들어 준다.
- 생성된 파일: `alembic/versions/9c9be169e6e1_create_posts_table.py`. 자동 생성이라도 **반드시 열어서 확인**한다.

## Spring이라면?

| SQLAlchemy / FastAPI | JPA / Spring |
|---|---|
| `engine` | `HikariDataSource` |
| `Session` | `EntityManager` (영속성 컨텍스트) |
| `class Post(Base)` + `Mapped[...]` | `@Entity` + `@Column` |
| `mapped_column(primary_key=True)` | `@Id @GeneratedValue` |
| `server_default=func.now()` | `@CreationTimestamp` |
| `onupdate=func.now()` | `@UpdateTimestamp` |
| `db.get(Post, id)` | `em.find(Post.class, id)` / `repository.findById(id)` |
| `db.add(post)` | `em.persist(post)` |
| `setattr(post, "title", v)` 후 `commit()` | 더티 체킹 (변경 감지 후 UPDATE) |
| **`db.commit()`을 직접 호출** | `@Transactional`이 메서드 끝에서 자동으로 해 주던 일 |
| `Depends(get_db)` | 요청 스코프 빈 주입 (`@PersistenceContext`) |
| Alembic | Flyway / Liquibase — 차이: autogenerate로 마이그레이션 초안을 **만들어 준다** |
| `app.dependency_overrides[get_db] = ...` | `@MockBean` / `@TestConfiguration`으로 빈 교체 |

**가장 중요한 차이:** Spring은 `@Transactional`이 커밋을 대신 해 주지만, 여기서는 `commit()`을 **직접** 불러야 한다.
`commit()` 없이 응답을 보내면 `get_db()`의 `finally`에서 세션이 닫히며 변경 사항이 사라진다.

## 디버깅 포인트

**`get_db()`의 실행 순서** — 01단계 `basics/generators.py`의 `get_session_like`와 나란히 놓고 보자.

```
요청 도착
 → FastAPI가 get_db()를 next()로 실행: db = SessionLocal() ... yield db 에서 멈춤
 → 엔드포인트 실행 (db를 인자로 받음)
 → 응답 생성
 → FastAPI가 get_db()를 이어서 실행: finally: db.close()
   (엔드포인트에서 예외가 나면 except: db.rollback() 후 다시 던짐)
```

**자주 보는 에러**

| 에러 | 원인 | 확인 |
|---|---|---|
| `psycopg.OperationalError: connection failed: ... port 5433 ... Connection refused` | DB 컨테이너가 꺼져 있다 | `docker compose ps`, `docker compose up -d --wait` |
| `psycopg.errors.UndefinedTable: relation "posts" does not exist` | 마이그레이션을 적용하지 않았다 | `uv run alembic upgrade head`, `uv run alembic current` |
| `psycopg.errors.NotNullViolation` | NOT NULL 컬럼에 None을 넣었다 | 어떤 필드가 None인지 트레이스백의 `[parameters: ...]` 확인 |
| 응답은 성공인데 데이터가 없다 | `commit()` 누락 | 07단계 실습 1번 |

**SQL 로그 보기:** `app/database.py`에서 `create_engine(DATABASE_URL, echo=True)`로 바꾸면 실행되는 SQL이 서버 로그에 찍힌다.
JPA의 `spring.jpa.show-sql=true`와 같다.

## 직접 해볼 것

1. `echo=True`로 바꾸고 서버를 띄운 뒤 POST 한 번에 어떤 SQL이 나가는지 로그로 확인한다.
   (`INSERT ... RETURNING posts.id, posts.created_at, ...` → `COMMIT` → `SELECT ...` 순서를 찾아본다)
2. `create_post`에서 `db.commit()`을 지우고 POST → 응답의 id로 GET을 해 본다. 무슨 일이 생기는가?
3. DB에 직접 접속해서 데이터를 본다.

   ```bash
   docker compose exec db psql -U board -d board
   board=# select * from posts;
   board=# select * from alembic_version;   -- Flyway의 flyway_schema_history와 같은 역할
   board=# \q
   ```

4. 끝나면 `git checkout -- app/`로 되돌린다.
