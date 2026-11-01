---
id: github-actions
title: Your First Pipeline with GitHub Actions
zone: delivery
edges:
  to:
    - id: build-and-test-pipeline
      question: >-
        I have a pipeline running. How do I make it properly test and build my
        code?
      detail: >-
        A basic 'hello world' pipeline is a start, but a real pipeline has
        structured stages: install dependencies, run tests, build the artifact,
        then deploy. Let's build that.
    - id: pipeline-secrets
      question: >-
        My pipeline needs to deploy to a server — it needs credentials. Where do
        I put secrets?
      detail: >-
        My pipeline needs to SSH into a server or push to a container registry.
        That means it needs credentials — but I can't just put SSH keys or
        passwords in the YAML file. Where do secrets like that even go, and how
        does the pipeline access them safely?
difficulty: 1
tags:
  - github-actions
  - ci-cd
  - yaml
  - pipelines
  - automation
category: tool
milestones:
  - Create a .github/workflows/ directory and write your first workflow YAML
  - Trigger a pipeline on push to main
  - Read the pipeline output in the GitHub Actions UI
  - 'Understand what a job, step, and runner are'
title_zh: "你的第一个 GitHub Actions 流水线"

---


GitHub Actions is a CI/CD platform built directly into GitHub. You describe your pipeline in a YAML file, commit it to your repo under `.github/workflows/`, and GitHub runs it automatically on every push — on their infrastructure, for free on public repos.

No separate CI service to sign up for, no webhooks to configure. Push code, pipeline runs, results appear in the Actions tab.

<!-- DEEP_DIVE -->

## The anatomy of a workflow

A workflow file lives at `.github/workflows/<name>.yml`. Every workflow has three parts: when to run (triggers), what machines to run on (runners), and what to do (jobs and steps).

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

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

- **`on`** — what triggers the workflow. `push` to main and any pull request.
- **`jobs`** — one or more parallel jobs. Each job gets a fresh runner.
- **`runs-on`** — the runner type. `ubuntu-latest` is the standard choice.
- **`steps`** — the sequence of commands within a job. Each step either uses a pre-built action (`uses:`) or runs a shell command (`run:`).

## Actions vs run steps

A **step** using `uses:` runs a pre-built Action from the marketplace. `actions/checkout@v4` clones your repo — you'd need it on almost every job. `actions/setup-python@v5` installs Python. Actions are reusable building blocks.

A **step** using `run:` executes shell commands directly. Anything you'd run in a terminal works here.

## Triggers

```yaml
on:
  push:
    branches: [main]        # only on pushes to main
  pull_request:             # on any PR (any branch)
  workflow_dispatch:        # adds a manual "Run workflow" button in the UI
  schedule:
    - cron: "0 6 * * *"     # daily at 6 AM UTC
```

`workflow_dispatch` is useful for manually triggering a pipeline (e.g. a deploy job you don't want running automatically).

## Reading the output

After a workflow runs, go to the **Actions** tab in your GitHub repo. You'll see a list of workflow runs, each tied to a commit. Click one to see the jobs. Click a job to see every step's output, including failure messages and exit codes.

When a step fails, the job stops, turns red, and GitHub sends you an email.

## Multiple jobs

Jobs run in parallel by default. Use `needs:` to chain them:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps: [...]

  deploy:
    runs-on: ubuntu-latest
    needs: test        # only runs if test passes
    steps: [...]
```

This is the foundation of a real pipeline: test first, deploy only if tests pass.

<!-- RESOURCES -->

- [GitHub Actions Documentation](https://docs.github.com/en/actions) -- type: reference, time: 20min
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions) -- type: reference, time: 10min

<!-- ZH_SUMMARY -->
GitHub Actions 是直接内置于 GitHub 的 CI/CD 平台。你在 YAML 文件中描述流水线，将其提交到仓库的 `.github/workflows/` 目录下，GitHub 便会在每次 push 时自动运行它——运行在 GitHub 的基础设施上，对公开仓库免费。

无需单独注册 CI 服务，也无需配置 webhook。推送代码，流水线即运行，结果会显示在 Actions 标签页中。

<!-- ZH_DEEP_DIVE -->
## 工作流的剖析

工作流文件位于 `.github/workflows/<name>.yml`。每个工作流都包含三个部分：何时运行（触发器）、在什么机器上运行（运行器），以及要做什么（作业和步骤）。

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

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

- **`on`** — 触发工作流的条件。推送到 main 分支以及任何拉取请求。
- **`jobs`** — 一个或多个并行作业。每个作业都会获得一个全新的运行器。
- **`runs-on`** — 运行器类型。`ubuntu-latest` 是标准选择。
- **`steps`** — 作业内命令的序列。每个步骤要么使用预构建的 action（`uses:`），要么运行 shell 命令（`run:`）。

## Actions 与 run 步骤

使用 `uses:` 的**步骤**会运行来自市场的预构建 Action。`actions/checkout@v4` 会克隆你的仓库——几乎每个作业都需要它。`actions/setup-python@v5` 会安装 Python。Actions 是可复用的构建块。

使用 `run:` 的**步骤**会直接执行 shell 命令。你在终端中能运行的任何内容都可以在这里运行。

## 触发器

```yaml
on:
  push:
    branches: [main]        # only on pushes to main
  pull_request:             # on any PR (any branch)
  workflow_dispatch:        # adds a manual "Run workflow" button in the UI
  schedule:
    - cron: "0 6 * * *"     # daily at 6 AM UTC
```

`workflow_dispatch` 对于手动触发流水线很有用（例如，你不希望自动运行的部署作业）。

## 读取输出

工作流运行后，转到 GitHub 仓库中的 **Actions** 标签页。你会看到工作流运行列表，每个运行都关联到一个提交。点击一个运行以查看作业。点击一个作业以查看每个步骤的输出，包括失败消息和退出码。

当某个步骤失败时，作业会停止、变红，GitHub 会向你发送电子邮件。

## 多个作业

作业默认并行运行。使用 `needs:` 将它们串联起来：

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps: [...]

  deploy:
    runs-on: ubuntu-latest
    needs: test        # only runs if test passes
    steps: [...]
```

这是真实流水线的基础：先测试，仅在测试通过后才部署。

<!-- ZH_RESOURCES -->
- [GitHub Actions 文档](https://docs.github.com/en/actions) -- 类型：参考，时间：20 分钟
- [GitHub Actions 市场](https://github.com/marketplace?type=actions) -- 类型：参考，时间：10 分钟

<!-- ZH_UI -->
1. 创建 .github/workflows/ 目录并编写你的第一个 workflow YAML
2. 在推送到 main 时触发流水线
3. 在 GitHub Actions UI 中查看流水线输出
4. 理解 job、step 和 runner 是什么
5. 我的流水线已经跑起来了。如何让它正确地测试和构建我的代码？
6. 一个基础的“hello world”流水线只是起点，真正的流水线有结构化的阶段：安装依赖、运行测试、构建产物，然后部署。我们来搭建它。
7. 我的流水线需要部署到服务器——它需要凭据。我把密钥放在哪里？
8. 我的流水线需要通过 SSH 登录服务器或推送到容器镜像仓库。这意味着它需要凭据——但我不能直接把 SSH 密钥或密码写进 YAML 文件。这类密钥到底该放在哪里，流水线又如何安全地访问它们？
