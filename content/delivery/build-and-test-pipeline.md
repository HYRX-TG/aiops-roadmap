---
id: build-and-test-pipeline
title: Build and Test in Your Pipeline
zone: delivery
edges:
  to:
    - id: containerization
      zone: containers
      question: >-
        Tests pass on every commit. How do I package the app to actually ship
        it?
      detail: >-
        My pipeline builds and tests the code, but it's still just source code
        in a repo. To actually ship it somewhere, I need to package it
        consistently. I've heard containers are the standard — but I'm not sure
        how that fits into a pipeline.
    - id: iac-intro
      question: >-
        My pipeline is solid. The servers it deploys to were set up by hand —
        can I codify that too?
      detail: >-
        I've automated the build and test, but the servers my app runs on were
        created by clicking through the cloud console. If they die or I need a
        second one, I'd have to recreate them manually. That feels wrong.
difficulty: 1
tags:
  - ci-cd
  - testing
  - pipelines
  - automation
  - github-actions
category: practice
milestones:
  - Run your test suite automatically on every push
  - Fail the pipeline if any test fails
  - Cache dependencies so the pipeline doesn't reinstall everything from scratch
  - Understand what a pipeline artifact is
title_zh: "在流水线中构建和测试"

---


A real CI pipeline has stages: install dependencies, run tests, build the artifact. Each stage must fail fast — if tests fail, nothing after them runs. You never ship untested code.

The goal is a pipeline that takes three minutes and gives you a clear green or red signal on every push.

<!-- DEEP_DIVE -->

## A complete test + build workflow

Here's a Python project as an example, but the shape is the same for any language:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest --tb=short

      - name: Lint
        run: ruff check .
```

The pipeline installs dependencies, runs the test suite, and lints the code. If any step returns a non-zero exit code, the job fails and stops.

## Caching dependencies

CI runners start fresh on every run. Without caching, `pip install` (or `npm install`, `bundle install`, etc.) downloads the entire dependency graph from scratch every time. On a large project, that's minutes.

`actions/cache` caches the package directory and restores it when the cache key matches. The key includes a hash of your lockfile — if `requirements.txt` changes, the cache is invalidated and dependencies are re-installed. If it hasn't changed, the cache is restored in seconds.

This alone can cut pipeline time by 50–80% for dependency-heavy projects.

## Fail fast, fail loud

Pipelines should fail at the earliest possible point. Don't run integration tests if unit tests fail. Don't build a Docker image if linting fails.

Structure your steps so the fastest checks run first:

1. Lint (seconds) — catches syntax errors and style issues immediately
2. Unit tests (fast) — catch logic errors without external dependencies
3. Integration tests (slower) — require databases, network, etc.
4. Build artifact — only runs if everything above passes

## Matrix builds

If your code needs to run on multiple Python versions, Node versions, or operating systems:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]

steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

GitHub runs a separate job for each matrix entry in parallel. If it fails on 3.12 but not 3.11, you know immediately.

## Pipeline artifacts

An artifact is a file produced by the pipeline that you want to keep — a compiled binary, a test coverage report, a built wheel. Upload them with `actions/upload-artifact`:

```yaml
- name: Upload coverage report
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: htmlcov/
```

Artifacts persist for 90 days by default and are downloadable from the Actions UI. For deployment pipelines, the built Docker image in a registry is the artifact — you don't need `upload-artifact` for images specifically.

<!-- RESOURCES -->

- [GitHub Actions: Caching Dependencies](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows) -- type: reference, time: 10min
- [GitHub Actions: Using a Matrix](https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs) -- type: reference, time: 10min

<!-- ZH_SUMMARY -->
一个真实的 CI 流水线包含多个阶段：安装依赖、运行测试、构建产物。每个阶段都必须快速失败——如果测试失败，其后的任何步骤都不会执行。绝不要发布未经测试的代码。

目标是打造一条耗时三分钟的流水线，并在每次推送时给出清晰的绿色或红色信号。

<!-- ZH_DEEP_DIVE -->
## 完整的测试 + 构建工作流

下面以一个 Python 项目为例，但任何语言的流水线结构都是相同的：

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest --tb=short

      - name: Lint
        run: ruff check .
```

该流水线会安装依赖、运行测试套件并对代码进行 lint 检查。如果任何一步返回非零退出码，作业就会失败并停止。

## 缓存依赖

CI runner 每次运行都从全新状态开始。如果不做缓存，`pip install`（或 `npm install`、`bundle install` 等）每次都会从头下载整个依赖图。在大型项目上，这要花好几分钟。

`actions/cache` 会缓存包目录，并在缓存键匹配时将其恢复。缓存键包含锁文件的哈希值——如果 `requirements.txt` 发生变化，缓存就会失效并重新安装依赖。如果它没有变化，缓存会在几秒内恢复。

仅这一项就能将依赖繁重项目的流水线时间缩短 50–80%。

## 快速失败，大声报错

流水线应尽可能早地失败。如果单元测试失败，就不要运行集成测试。如果 lint 检查失败，就不要构建 Docker 镜像。

合理安排步骤顺序，让最快的检查先运行：

1. Lint（几秒）——立即捕获语法错误和风格问题
2. 单元测试（快）——无需外部依赖即可捕获逻辑错误
3. 集成测试（较慢）——需要数据库、网络等
4. 构建产物——仅当以上全部通过时才运行

## 矩阵构建

如果你的代码需要在多个 Python 版本、Node 版本或操作系统上运行：

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]

steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

GitHub 会为每个矩阵条目并行运行一个独立作业。如果它在 3.12 上失败但在 3.11 上通过，你立刻就能知道。

## 流水线产物

产物是流水线生成、你希望保留的文件——编译后的二进制文件、测试覆盖率报告、构建好的 wheel。使用 `actions/upload-artifact` 上传它们：

```yaml
- name: Upload coverage report
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: htmlcov/
```

产物默认保留 90 天，可从 Actions UI 下载。对于部署流水线，注册表中构建好的 Docker 镜像就是产物——镜像本身不需要使用 `upload-artifact`。

<!-- ZH_RESOURCES -->
- [GitHub Actions：缓存依赖](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows) -- 类型：参考，时间：10 分钟
- [GitHub Actions：使用矩阵](https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs) -- 类型：参考，时间：10 分钟

<!-- ZH_UI -->
1. 每次推送时自动运行测试套件
2. 任何测试失败则使流水线失败
3. 缓存依赖，避免流水线每次从头重新安装
4. 理解什么是流水线产物
5. 每次提交测试都通过。我该如何打包应用才能真正发布它？
6. 我的流水线会构建并测试代码，但它仍然只是仓库里的源代码。要真正把它发布到某处，我需要一致地打包它。我听说容器是标准做法——但我不确定它如何融入流水线。
7. 我的流水线很可靠。它部署到的服务器是手工搭建的——我能否也把这写成代码？
8. 我已经自动化了构建和测试，但应用运行的服务器是通过点击云控制台创建的。如果它们挂了或者我需要第二台，我就得手动重建。这感觉不对。
