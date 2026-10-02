from basics.decorators import CALL_LOG, MiniRouter, add


def test_log_calls_wraps_function():
    CALL_LOG.clear()
    assert add(1, 2) == 3
    assert CALL_LOG == ["add called with (1, 2)", "add returned 3"]


def test_functools_wraps_keeps_name():
    assert add.__name__ == "add"


def test_mini_router_registers_handlers():
    router = MiniRouter()

    @router.get("/health")
    def health():
        return {"status": "ok"}

    assert router.handle("/health") == (200, {"status": "ok"})
    assert router.handle("/nope") == (404, None)
    # 데코레이터가 원래 함수를 그대로 돌려주므로 직접 호출도 된다
    assert health() == {"status": "ok"}
