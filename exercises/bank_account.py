"""연습 문제: 아래 Java 코드를 Python으로 옮기세요.

채점: uv run pytest exercises -v

```java
public class InsufficientBalanceException extends RuntimeException {
    private final int balance;
    private final int amount;

    public InsufficientBalanceException(int balance, int amount) {
        super("잔액 부족: 잔액 " + balance + ", 요청 " + amount);
        this.balance = balance;
        this.amount = amount;
    }
    // getBalance(), getAmount() 생략
}

public class BankAccount {
    private final String owner;
    private int balance;

    public BankAccount(String owner) {
        this(owner, 0);
    }

    public BankAccount(String owner, int balance) {
        if (balance < 0) {
            throw new IllegalArgumentException("초기 잔액은 0 이상이어야 합니다");
        }
        this.owner = owner;
        this.balance = balance;
    }

    public String getOwner() { return owner; }

    public int getBalance() { return balance; }   // 읽기만 가능, setBalance 없음

    public int deposit(int amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("입금액은 0보다 커야 합니다");
        }
        this.balance += amount;
        return this.balance;
    }

    public int withdraw(int amount) {
        if (amount > this.balance) {
            throw new InsufficientBalanceException(this.balance, amount);
        }
        this.balance -= amount;
        return this.balance;
    }

    @Override
    public String toString() {
        return "BankAccount(owner=" + owner + ", balance=" + balance + ")";
    }
}
```

요구 사항 (테스트가 확인하는 것)
- 생성자 오버로딩 2개를 __init__ 하나로 합친다.
- account.owner, account.balance 로 읽을 수 있다 (괄호 없이).
- account.balance = 999 처럼 직접 바꾸려 하면 AttributeError가 나야 한다.
- IllegalArgumentException 은 Python 내장 예외 ValueError 로 바꾼다.
- 출금 실패 예외는 메시지와 함께 .balance, .amount 값을 갖는다.
- print(account) 결과가 toString()과 같다. 예: BankAccount(owner=홍길동, balance=1000)
"""


class InsufficientBalanceError(Exception):
    def __init__(self, balance: int, amount: int) -> None:
        super().__init__(f"잔액 부족: 잔액 {balance}, 요청 {amount}")
        self.balance = balance
        self.amount = amount


class BankAccount:
    def __init__(self, owner: str, balance: int = 0) -> None:
        if balance < 0:
            raise ValueError("초기 잔액은 0 이상이어야 합니다")
        self.owner = owner
        self._balance = balance

    def deposit(self, amount: int) -> int:
        if amount <= 0:
            raise ValueError("입금액은 0보다 커야 합니다")
        self._balance += amount
        return self._balance

    def withdraw(self, amount: int) -> int:
        if amount > self._balance:
            raise InsufficientBalanceError(self._balance, amount)
        self._balance -= amount
        return self._balance

    def __repr__(self) -> str:
        return f"BankAccount(owner={self.owner}, balance={self._balance})"

    @property
    def balance(self) -> int:
        return self._balance
