---
name: testrules
description: Production-grade test case writing rules for AutoDebug. Referenced by autodebug skill when write-testcase flag is passed.
triggers: []
tools: []
when-to-use: Internal rules file — loaded by /autodebug when write-testcase flag is passed. Not invoked directly.
argument-hint: ""
arguments: []
context: inline
source: user
---

# AutoDebug Test Rules

Loaded when `/autodebug write-testcase` is invoked. These rules govern how test cases are written for every finding.

---

## STEP 0: DISCOVER EXISTING TEST PATTERNS

Before writing ANY test, scan the repo to understand how tests are already written.

### 0.1 Find the test directory
- `get_file_tree` with `path_prefix="tests/"` or `path_prefix="test/"` or `path_prefix="__tests__/"`
- Also check: `src/**/*.test.*`, `src/**/*.spec.*`, `**/*_test.py`, `**/*Test.java`
- If no test directory exists: create one following language convention (see §0.3)

### 0.2 Read existing test files
- `get_file_outline` on 3-5 existing test files
- `get_symbol_source` on representative test functions
- Extract and record these patterns:

| Pattern | What To Look For |
|---------|-----------------|
| **Framework** | pytest, unittest, Jest, Vitest, Mocha, JUnit, Go testing, etc. |
| **File naming** | `test_*.py`, `*.test.ts`, `*_test.go`, `*Test.java` |
| **Structure** | Class-based (unittest, JUnit) vs function-based (pytest, Jest) |
| **Fixtures** | pytest fixtures, Jest beforeEach/afterEach, Go t.Cleanup |
| **Mocking** | unittest.mock, jest.mock(), gomock, testcontainers |
| **Assertions** | assert, expect(), assert.Equal, should |
| **Data setup** | Factory pattern, seed scripts, inline data, fakers |
| **DB handling** | Transactions rolled back, test DB, SQLite in-memory, Docker |
| **Async handling** | pytest-asyncio, async/await in Jest, goroutines |
| **Coverage tool** | pytest-cov, jest --coverage, go test -cover |
| **Snapshot testing** | Jest snapshots, pytest-snapshot |
| **CI integration** | GitHub Actions, Makefile targets, npm scripts |

### 0.3 Language-specific test directory conventions

If NO existing tests found, use these defaults:

| Language | Directory | File Pattern | Framework |
|----------|-----------|-------------|-----------|
| Python | `tests/` | `test_*.py` | pytest |
| TypeScript/JS | `__tests__/` or `src/**/*.test.ts` | `*.test.ts` | Jest or Vitest |
| Go | Same package | `*_test.go` | Go testing |
| Java | `src/test/java/` | `*Test.java` | JUnit 5 |
| Rust | Same directory | `*_test.rs` mod tests | built-in |
| Ruby | `spec/` or `test/` | `*_spec.rb` | RSpec |

---

## STEP 1: PRODUCTION-GRADE TEST PRINCIPLES

Every test written MUST follow these principles. No exceptions.

### 1.1 The 7 Rules of Production Tests

1. **Deterministic** — Same input → same output, every time. No `Math.random()`, no `datetime.now()`, no network calls. Mock/seed all non-deterministic sources.
2. **Isolated** — Each test runs independently. No shared mutable state. No test ordering dependencies. Use fresh fixtures or transactions rolled back.
3. **Fast** — Unit tests < 100ms. Integration tests < 5s. If slower, mock the slow part. No real HTTP calls, no real DB writes in unit tests.
4. **Named by behavior** — Test name describes WHAT is being tested and WHAT the expected outcome is. Not `testFunction1`. Use: `test_user_login_with_invalid_password_returns_401`
5. **Assert one behavior** — One logical assertion per test. Multiple physical assertions on the same object are fine. Testing multiple behaviors in one test is not.
6. **No implementation coupling** — Test the PUBLIC interface, not private methods. If you refactor internals, tests should still pass. Test WHAT, not HOW.
7. **Meaningful failures** — Assertion messages must explain what was expected vs what happened. Not "assertion failed". Use: `assertEqual(result, expected, f"Expected 401 for invalid password, got {result}")`

### 1.2 Test Categories — Write the Right Type

| Category | When | Scope | Mocking |
|----------|------|-------|---------|
| **Unit** | Pure logic, data transforms, validation | Single function/class | All dependencies mocked |
| **Integration** | API endpoints, DB operations, service-to-service | Module boundary | Real DB (test), real services (test env) |
| **Contract** | API contracts, schema validation | Interface boundary | Minimal mocking |
| **E2E** | Critical user flows | Full system | None (test environment) |
| **Regression** | Bugs found by autodebug | Specific bug reproduction | Minimal — reproduce the exact bug |

### 1.3 Test Structure (AAA Pattern)

```
def test_<behavior>():
    # ARRANGE — set up preconditions
    user = User(name="test", role="admin")
    db.save(user)

    # ACT — execute the thing being tested
    result = service.delete_user(user.id)

    # ACT — assert the outcome
    assert result.status == 200
    assert db.get(user.id) is None
```

---

## STEP 2: TEST GENERATION PER FINDING CATEGORY

### 2.1 Security Findings → Security Regression Tests

```python
# For SQL injection finding:
def test_user_search_rejects_sql_injection():
    malicious_input = "'; DROP TABLE users; --"
    response = client.get(f"/api/users?name={malicious_input}")
    assert response.status_code == 400
    # Verify table still exists
    assert db.query("SELECT count(*) FROM users") is not None

# For XSS finding:
def test_profile_render_escapes_script_tags():
    payload = '<script>alert("xss")</script>'
    user = create_user(bio=payload)
    html = render_profile(user)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
```

### 2.2 Logic Bug Findings → Boundary + Edge Case Tests

```python
# For off-by-one finding:
def test_pagination_last_page_returns_remaining_items():
    total = 53
    page_size = 10
    last_page = paginate(total, page=6, size=page_size)
    assert len(last_page) == 3  # not 10, not 0

# For null check finding:
def test_process_order_handles_missing_customer():
    order = Order(customer_id=None)
    result = process_order(order)
    assert result.status == "error"
    assert "customer required" in result.message
```

### 2.3 Performance Findings → Performance Regression Tests

```python
# For N+1 query finding:
def test_user_list_no_n_plus_one_queries():
    create_users(100)
    with assert_max_queries(expected=3):  # 1 for users, 1 for roles, 1 for prefs
        response = client.get("/api/users")
    assert response.status_code == 200

# For unbounded query finding:
def test_api_returns_paginated_results():
    create_users(5000)
    response = client.get("/api/users")
    assert len(response.json()) <= 100
    assert "next_page" in response.json()
```

### 2.4 Dead Code Findings → Deletion Confirmation Tests

```python
# For dead code finding — write a test that WOULD break if the code is actually needed:
def test_dead_function_can_be_removed():
    # If this function IS actually used somewhere, this test documents it:
    with pytest.raises(AttributeError):
        # Confirm it's not imported anywhere critical
        result = check_importers("unused_helper_function")
        assert result.is_safe_to_delete
```

### 2.5 DB Findings → Schema + Query Tests

```python
# For missing index finding:
def test_user_query_by_email_uses_index():
    explain = db.query("EXPLAIN SELECT * FROM users WHERE email = 'test@test.com'")
    assert "Using index" in str(explain)
    assert "Using filesort" not in str(explain)
    assert "Full table scan" not in str(explain)
```

### 2.6 Type Safety Findings → Type Boundary Tests

```python
# For missing null check on typed parameter:
def test_calculate_discount_handles_zero_price():
    with pytest.raises(ValueError, match="price must be positive"):
        calculate_discount(price=0, discount_pct=10)

def test_calculate_discount_handles_negative_price():
    with pytest.raises(ValueError):
        calculate_discount(price=-100, discount_pct=10)
```

---

## STEP 3: TEST FILE ORGANIZATION

### 3.1 Where to Write Tests

- Match the source file structure 1:1 in the test directory
- `src/services/user_service.py` → `tests/services/test_user_service.py`
- `src/routes/api.ts` → `__tests__/routes/api.test.ts`

### 3.2 Output Location

When `write-testcase` is active, write tests to:

```
debug_output/
├── 001-security-sql-injection.md          # Finding (always written)
├── 001-security-sql-injection.test.py      # Test for finding (only with write-testcase)
├── 002-logic-off-by-one.md                # Finding
├── 002-logic-off-by-one.test.py           # Test for finding
└── ...
```

### 3.3 Test File Header

Every generated test file starts with:

```python
"""
AutoDebug-generated regression test.
Finding: [CATEGORY] [TITLE]
Severity: [SEVERITY]
Original file: [SOURCE_FILE]
Generated: [TIMESTAMP]

Run with: pytest [testfile] -v
"""
```

---

## STEP 4: MOCKING STRATEGY — PRODUCTION GRADE

### 4.1 What to Mock

| Mock It | Don't Mock It |
|---------|---------------|
| External APIs (Stripe, SendGrid) | Business logic |
| Database (in unit tests) | Data validation |
| File system (in unit tests) | Serialization format |
| Time (`datetime.now`, `time.time`) | Time parsing/formatting |
| Random (`random.random`, `uuid`) | Deterministic algorithms |
| Network calls | Error handling of network failures |

### 4.2 Mock Quality Rules

1. **Mocks must be minimal** — Only mock what the test needs. Don't create a 50-field mock object when the test uses 3 fields.
2. **Mocks must be realistic** — Use production-like data shapes. If an API returns `{id: number, name: string}`, don't mock it with `{id: "abc"}`.
3. **Mocks must be explicit** — No `MagicMock()` without configuring return values. Every mock behavior is intentional and documented by the test.
4. **Use fakers for data** — Use `faker`, `factory_boy`, `Faker.js` for test data that needs to look realistic. Use `seed(42)` for reproducibility.
5. **Clean up mocks** — Every mock is restored after the test. Use `@patch` decorators, `beforeEach` cleanup, or context managers. Never let a mock leak into another test.

### 4.3 Database Testing Strategy

```
Unit tests:       Mock the DB layer entirely
Integration:      Use a real test DB with transactions rolled back after each test
E2E:              Use testcontainers or a dedicated test DB instance

NEVER run integration tests against production or staging DB.
```

---

## STEP 5: ASSERTION QUALITY

### 5.1 Bad vs Good Assertions

```python
# BAD — vague, unhelpful on failure
assert result
assert len(items) > 0
assert response.status_code == 200

# GOOD — specific, helpful on failure
assert result.status == "completed", f"Expected 'completed', got '{result.status}'"
assert len(items) == 3, f"Expected 3 items, got {len(items)}: {[i.name for i in items]}"
assert response.status_code == 401, f"Unauthenticated request should return 401, got {response.status_code}"
```

### 5.2 Negative Testing

Every positive test (happy path) should have a corresponding negative test:

| Happy Path | Negative Counterpart |
|-----------|---------------------|
| Valid input returns 200 | Invalid input returns 400 |
| Authenticated user can access | Unauthenticated user gets 401 |
| Authorized role can modify | Unauthorized role gets 403 |
| Existing resource found | Missing resource returns 404 |
| Proper format accepted | Malformed input rejected |
| Concurrent access succeeds | Race condition handled |

---

## STEP 6: LANGUAGE-SPECIFIC PRODUCTION PATTERNS

### 6.1 Python (pytest)

```python
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

@pytest.fixture
def user(db):
    user = User(email="test@example.com", name="Test User")
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def frozen_time():
    with patch("module.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 15, 12, 0, 0)
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
        yield mock_dt

class TestUserCreation:
    def test_valid_user_created_successfully(self, db, user):
        assert user.id is not None
        assert user.email == "test@example.com"

    def test_duplicate_email_rejected(self, db, user):
        with pytest.raises(IntegrityError):
            User(email=user.email, name="Duplicate")

    def test_invalid_email_format_rejected(self, db):
        with pytest.raises(ValidationError):
            User(email="not-an-email", name="Bad Email")
```

### 6.2 TypeScript (Jest/Vitest)

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { UserService } from './user.service';

describe('UserService', () => {
  let service: UserService;
  let mockRepo: any;

  beforeEach(() => {
    mockRepo = { findById: vi.fn(), save: vi.fn() };
    service = new UserService(mockRepo);
  });

  it('returns user when found', async () => {
    mockRepo.findById.mockResolvedValue({ id: 1, name: 'Test' });
    const result = await service.getUser(1);
    expect(result).toEqual({ id: 1, name: 'Test' });
  });

  it('throws NotFound when user missing', async () => {
    mockRepo.findById.mockResolvedValue(null);
    await expect(service.getUser(999)).rejects.toThrow(NotFoundError);
  });
});
```

### 6.3 Go

```go
func TestUserCreation(t *testing.T) {
    tests := []struct {
        name    string
        input   CreateUserInput
        wantErr error
    }{
        {"valid user", CreateUserInput{Name: "Test", Email: "t@t.com"}, nil},
        {"missing email", CreateUserInput{Name: "Test"}, ErrValidation},
        {"duplicate email", CreateUserInput{Name: "Test", Email: "existing@test.com"}, ErrConflict},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            _, err := CreateUser(tt.input)
            if !errors.Is(err, tt.wantErr) {
                t.Errorf("got %v, want %v", err, tt.wantErr)
            }
        })
    }
}
```

---

## STEP 7: QUALITY CHECKLIST

Before writing any test file, verify ALL of these:

- [ ] Test follows existing repo patterns (from Step 0)
- [ ] Test name describes behavior, not implementation
- [ ] Test is deterministic (no random, no network, no current time)
- [ ] Test is isolated (no shared mutable state with other tests)
- [ ] Test is fast (< 100ms for unit, < 5s for integration)
- [ ] Test uses AAA pattern (Arrange, Act, Assert)
- [ ] Test has meaningful failure messages
- [ ] Negative test case included alongside positive case
- [ ] Mocks are minimal, realistic, explicit, and cleaned up
- [ ] Test actually reproduces the bug found by autodebug
- [ ] Test would FAIL if the bug is present and PASS after the fix
- [ ] Test file is in the correct location matching repo structure
