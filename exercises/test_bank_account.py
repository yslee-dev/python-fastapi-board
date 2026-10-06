import pytest

from exercises.bank_account import BankAccount, InsufficientBalanceError

# --- 생성자 (__init__) ---


def test_create_with_default_balance():
    account = BankAccount("홍길동")

    assert account.owner == "홍길동"
    assert account.balance == 0


def test_create_with_initial_balance():
    account = BankAccount("홍길동", 1000)

    assert account.balance == 1000


def test_create_with_keyword_argument():
    account = BankAccount(owner="홍길동", balance=500)

    assert account.balance == 500


def test_create_rejects_negative_balance():
    with pytest.raises(ValueError):
        BankAccount("홍길동", -1)


# --- 입금 / 출금 ---


def test_deposit_returns_new_balance():
    account = BankAccount("홍길동", 1000)

    assert account.deposit(500) == 1500
    assert account.balance == 1500


@pytest.mark.parametrize("amount", [0, -100])
def test_deposit_rejects_non_positive_amount(amount):
    account = BankAccount("홍길동", 1000)

    with pytest.raises(ValueError):
        account.deposit(amount)
    assert account.balance == 1000


def test_withdraw_returns_new_balance():
    account = BankAccount("홍길동", 1000)

    assert account.withdraw(300) == 700


def test_withdraw_can_empty_the_account():
    account = BankAccount("홍길동", 1000)

    assert account.withdraw(1000) == 0


def test_withdraw_more_than_balance_raises_custom_error():
    account = BankAccount("홍길동", 1000)

    with pytest.raises(InsufficientBalanceError) as exc_info:
        account.withdraw(5000)

    error = exc_info.value
    assert str(error) == "잔액 부족: 잔액 1000, 요청 5000"
    assert error.balance == 1000
    assert error.amount == 5000
    assert account.balance == 1000  # 실패하면 잔액은 그대로


# --- 캡슐화 ---


def test_balance_cannot_be_assigned_directly():
    account = BankAccount("홍길동", 1000)

    with pytest.raises(AttributeError):
        account.balance = 999


def test_each_account_has_its_own_balance():
    a = BankAccount("A", 100)
    b = BankAccount("B", 100)

    a.deposit(50)

    assert a.balance == 150
    assert b.balance == 100


# --- toString ---


def test_repr_matches_java_to_string():
    account = BankAccount("홍길동", 1000)

    assert repr(account) == "BankAccount(owner=홍길동, balance=1000)"
    assert str(account) == "BankAccount(owner=홍길동, balance=1000)"
