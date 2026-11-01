---
id: testing-basics
title: Testing Your Code
zone: building
edges:
  to:
    - id: it-works-on-my-laptop
      question: >-
        My code is tested and I'm confident it works. Now how do I run it
        somewhere real?
      detail: >-
        My tests pass locally. But I have no idea if they'd still pass in
        whatever environment I'm deploying to — different OS, different Python
        version, different database. And I'm not sure how to even get the code
        running on a real server in the first place.
difficulty: 1
tags:
  - testing
  - unit-tests
  - integration-tests
  - pytest
  - tdd
category: concept
milestones:
  - Write unit tests for a Python function using pytest
  - Write an integration test that tests an API endpoint end-to-end
  - 'Understand the testing pyramid: unit, integration, and end-to-end tests'
title_zh: "测试你的代码"

---


You changed one function and broke three other features. You did not know until a user reported it two days later. The fix took five minutes, but the debugging took two hours. Automated tests would have caught it in seconds — before the code ever left your laptop.

<!-- DEEP_DIVE -->

**Automated testing** means writing code that tests your code. Instead of manually clicking through your app, you write functions that call your code, check the results, and tell you if something is wrong. Tests run in seconds and catch regressions (things that used to work but broke) immediately.

**pytest** is the standard testing framework for Python. A test is just a function that starts with `test_`:

```python
# calculator.py
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

```python
# test_calculator.py
import pytest
from calculator import add, divide

def test_add_basic():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, 1) == 0

def test_divide_basic():
    assert divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
```

```bash
# Run the tests
$ pytest test_calculator.py -v
test_calculator.py::test_add_basic PASSED
test_calculator.py::test_add_negative PASSED
test_calculator.py::test_divide_basic PASSED
test_calculator.py::test_divide_by_zero PASSED

4 passed in 0.02s
```

**The testing pyramid** describes three levels of tests:

**Unit tests** are at the base — small, fast, and numerous. They test a single function or class in isolation. If your `calculate_tax()` function is wrong, a unit test catches it immediately. They run in milliseconds and you should have hundreds of them:

```python
def test_calculate_tax():
    assert calculate_tax(100, rate=0.08) == 8.0
    assert calculate_tax(0, rate=0.08) == 0.0
    assert calculate_tax(100, rate=0) == 0.0
```

**Integration tests** are in the middle — they test how components work together. Does your API endpoint correctly query the database and return the right response? These are slower because they involve real databases, HTTP requests, or file systems:

```python
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

def test_create_user(client):
    response = client.post("/api/users", json={
        "name": "Alice",
        "email": "alice@example.com"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Alice"

def test_get_nonexistent_user(client):
    response = client.get("/api/users/999")
    assert response.status_code == 404
```

**End-to-end (E2E) tests** are at the top — they test the entire system from the user's perspective. A browser automation tool clicks through your app just like a real user would. They are slow, flaky, and expensive, so you write fewer of them — just enough to verify the critical paths (signup, checkout, login).

**What to test and what not to:**

- **Test:** Business logic, edge cases, error handling, data transformations
- **Test:** API contracts (correct status codes, response shapes)
- **Don't test:** Framework internals (Flask's routing, SQLAlchemy's query builder)
- **Don't test:** Trivial getters/setters with no logic

**Fixtures** in pytest set up the context your tests need — a database connection, a test client, sample data:

```python
@pytest.fixture
def sample_user():
    return {"name": "Alice", "email": "alice@example.com"}

def test_user_has_email(sample_user):
    assert "@" in sample_user["email"]
```

**Why SREs care:** Tests are the first line of defense against outages. A comprehensive test suite means changes can be deployed with confidence. In SRE culture, tests are part of the deployment pipeline — if tests fail, the deployment stops. You will also write tests for infrastructure code (Terraform modules, Ansible playbooks, monitoring rules). The concept is the same: verify that things work before they hit production.

<!-- RESOURCES -->

- [pytest Documentation](https://docs.pytest.org/en/stable/) -- type: reference, time: varies
- [Python Testing with pytest (book)](https://pragprog.com/titles/bopytest2/python-testing-with-pytest-second-edition/) -- type: book, time: varies
- [Testing Flask Applications](https://flask.palletsprojects.com/en/stable/testing/) -- type: tutorial, time: 30m
- [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) -- type: article, time: 30m

<!-- ZH_SUMMARY -->
你改了一个函数，却破坏了另外三个功能。直到两天后用户反馈，你才发现问题。修复只花了五分钟，调试却花了两个小时。自动化测试本可以在几秒内发现它——在代码离开你的笔记本电脑之前。

<!-- ZH_DEEP_DIVE -->
**自动化测试**指的是编写用来测试你的代码的代码。你不再手动点击应用，而是编写函数来调用你的代码、检查结果，并告诉你哪里出了问题。测试在几秒内就能运行完成，并立即捕获回归（以前能正常工作但现在坏掉的功能）。

**pytest** 是 Python 的标准测试框架。一个测试就是一个以 `test_` 开头的函数：

```python
# calculator.py
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

```python
# test_calculator.py
import pytest
from calculator import add, divide

def test_add_basic():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, 1) == 0

def test_divide_basic():
    assert divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
```

```bash
# Run the tests
$ pytest test_calculator.py -v
test_calculator.py::test_add_basic PASSED
test_calculator.py::test_add_negative PASSED
test_calculator.py::test_divide_basic PASSED
test_calculator.py::test_divide_by_zero PASSED

4 passed in 0.02s
```

**测试金字塔**描述了三个层次的测试：

**单元测试**位于底层——规模小、速度快、数量多。它们隔离地测试单个函数或类。如果你的 `calculate_tax()` 函数写错了，单元测试会立即捕获它。它们在毫秒级运行完成，你应该有数百个这样的测试：

```python
def test_calculate_tax():
    assert calculate_tax(100, rate=0.08) == 8.0
    assert calculate_tax(0, rate=0.08) == 0.0
    assert calculate_tax(100, rate=0) == 0.0
```

**集成测试**位于中间层——它们测试各个组件如何协同工作。你的 API 端点是否正确查询数据库并返回正确的响应？这类测试较慢，因为它们涉及真实的数据库、HTTP 请求或文件系统：

```python
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

def test_create_user(client):
    response = client.post("/api/users", json={
        "name": "Alice",
        "email": "alice@example.com"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Alice"

def test_get_nonexistent_user(client):
    response = client.get("/api/users/999")
    assert response.status_code == 404
```

**端到端（E2E）测试**位于顶层——它们从用户视角测试整个系统。浏览器自动化工具会像真实用户一样点击浏览你的应用。这类测试速度慢、不稳定且成本高，所以你应该少写一些——只写足够验证关键路径（注册、结账、登录）的数量即可。

**该测试什么、不该测试什么：**

- **测试：** 业务逻辑、边界情况、错误处理、数据转换
- **测试：** API 契约（正确的状态码、响应结构）
- **不要测试：** 框架内部实现（Flask 的路由、SQLAlchemy 的查询构建器）
- **不要测试：** 没有逻辑的简单 getter/setter

pytest 中的 **fixture** 用于搭建测试所需的上下文——数据库连接、测试客户端、示例数据：

```python
@pytest.fixture
def sample_user():
    return {"name": "Alice", "email": "alice@example.com"}

def test_user_has_email(sample_user):
    assert "@" in sample_user["email"]
```

**为什么 SRE 关心这件事：** 测试是防御故障的第一道防线。一套全面的测试意味着可以放心地部署变更。在 SRE 文化中，测试是部署流水线的一部分——如果测试失败，部署就会停止。你还需要为基础设施代码（Terraform 模块、Ansible playbook、监控规则）编写测试。概念是一样的：在进入生产环境之前验证一切正常工作。

<!-- ZH_RESOURCES -->
- [pytest 文档](https://docs.pytest.org/en/stable/) -- 类型：参考，时间：不定
- [使用 pytest 进行 Python 测试（书籍）](https://pragprog.com/titles/bopytest2/python-testing-with-pytest-second-edition/) -- 类型：书籍，时间：不定
- [测试 Flask 应用](https://flask.palletsprojects.com/en/stable/testing/) -- 类型：教程，时间：30 分钟
- [实用测试金字塔](https://martinfowler.com/articles/practical-test-pyramid.html) -- 类型：文章，时间：30 分钟

<!-- ZH_UI -->
1. 使用 pytest 为 Python 函数编写单元测试
2. 编写一个端到端测试 API 端点的集成测试
3. 理解测试金字塔：单元测试、集成测试和端到端测试
4. 我的代码已经过测试，我确信它能正常工作。现在如何在一个真实环境中运行它？
5. 我的测试在本地通过。但我不知道它们在我要部署到的环境中是否仍能通过——不同的操作系统、不同的 Python 版本、不同的数据库。而且我甚至不确定如何首先让代码在真实服务器上运行起来。
