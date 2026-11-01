---
id: pipeline-secrets
title: Secrets in CI/CD Pipelines
zone: delivery
edges:
  to:
    - id: build-and-test-pipeline
      question: Secrets are handled. Now how do I structure the full pipeline?
      detail: >-
        I have the credentials in the right place, but my pipeline still only
        runs tests. I want the whole thing — test, build the image, push it, and
        actually deploy — all in one automated flow.
difficulty: 2
tags:
  - secrets
  - security
  - ci-cd
  - environment-variables
  - github-secrets
  - vault
category: practice
milestones:
  - Store a secret in GitHub Actions secrets and reference it in a workflow
  - Understand why secrets should never appear in logs or YAML files
  - Know the difference between repository secrets and environment secrets
title_zh: "CI/CD 流水线中的密钥"

---


Your pipeline needs to SSH into servers, push Docker images to a registry, or call external APIs. All of those require credentials. Those credentials must never appear in your YAML files or commit history.

GitHub Actions has a built-in encrypted secret store. Secrets are injected as environment variables at runtime — your pipeline code can use them, but they're never written to disk or printed in logs.

<!-- DEEP_DIVE -->

## Why not just put them in the YAML?

Git is permanent. If you commit a secret — even for one minute, even in a private repo — it's in the history. Tools like `git log`, `git reflog`, and automated secret scanners will find it. Rotating the secret and scrubbing the history is painful. Avoiding the problem is not.

The rule: **credentials never touch your repository.** Not in YAML, not in `.env` files, not in comments.

## GitHub Actions secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

Give it a name (by convention, `UPPER_SNAKE_CASE`) and a value. GitHub encrypts it. You can't read the value back — only update or delete it.

Reference it in your workflow with `${{ secrets.YOUR_SECRET_NAME }}`:

```yaml
- name: Deploy to server
  env:
    DEPLOY_KEY: ${{ secrets.DEPLOY_SSH_KEY }}
  run: |
    echo "$DEPLOY_KEY" > /tmp/deploy_key
    chmod 600 /tmp/deploy_key
    ssh -i /tmp/deploy_key user@yourserver.com "cd /app && ./deploy.sh"
```

GitHub automatically masks the secret value in logs. If it appears in output, it shows as `***`.

## Repository vs environment secrets

**Repository secrets** are available to all workflows in the repo. Use these for things like registry credentials that every pipeline needs.

**Environment secrets** are scoped to a named environment (e.g. `staging`, `production`). A job must declare `environment: production` to access them. This lets you require approval before a job can access production credentials:

```yaml
jobs:
  deploy-production:
    environment: production    # can require manual approval in settings
    steps:
      - run: deploy.sh
        env:
          API_KEY: ${{ secrets.PROD_API_KEY }}
```

For anything touching production, environment secrets with required reviewers are worth the extra setup.

## Organization secrets

If you manage multiple repos, organization secrets let you share credentials across all repos (or a subset) without duplicating them. Set them at the organization level under Settings → Secrets.

## What gets masked, what doesn't

GitHub masks the exact secret value if it appears in logs. It doesn't mask derived values — if your secret is `abc123` and your script prints `MY_TOKEN=abc123`, it will be masked. But if the script encodes it to base64 and prints that, it won't be.

Don't print secrets in logs. Add `set +x` before any command that uses a secret if you're running `set -x` for debugging.

## SSH key pattern

For SSH-based deploys, the common pattern:

1. Generate a dedicated key pair for CI: `ssh-keygen -t ed25519 -C "ci-deploy" -f deploy_key`
2. Add the **public key** to `~/.ssh/authorized_keys` on your server
3. Store the **private key** as a GitHub Actions secret
4. In the workflow, write it to a temp file and use it for SSH

Never reuse your personal SSH key for CI. A dedicated key can be rotated or revoked without disrupting your own access.

<!-- RESOURCES -->

- [GitHub Actions: Using Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions) -- type: reference, time: 10min
- [GitHub Actions: Using Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment) -- type: reference, time: 10min

<!-- ZH_SUMMARY -->
你的流水线需要 SSH 登录服务器、将 Docker 镜像推送到镜像仓库，或调用外部 API。所有这些操作都需要凭据。这些凭据绝不能出现在你的 YAML 文件或提交历史中。

GitHub Actions 内置了加密的密钥存储。密钥在运行时以环境变量的形式注入——你的流水线代码可以使用它们，但它们永远不会被写入磁盘或打印到日志中。

<!-- ZH_DEEP_DIVE -->
## 为什么不直接把它们放进 YAML 里？

Git 是永久的。如果你提交了一个 secret——哪怕只有一分钟，哪怕是在私有仓库里——它都会留在历史记录中。`git log`、`git reflog` 以及自动化 secret 扫描工具都能找到它。轮换 secret 并清理历史记录非常痛苦。而避免这个问题则并不痛苦。

规则是：**凭据永远不要碰你的仓库。** 不要放在 YAML 里，不要放在 `.env` 文件里，也不要放在注释里。

## GitHub Actions secrets

进入你的仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**。

给它起一个名字（按惯例使用 `UPPER_SNAKE_CASE`）和一个值。GitHub 会对其进行加密。你无法再读回该值——只能更新或删除它。

在工作流中用 `${{ secrets.YOUR_SECRET_NAME }}` 引用它：

```yaml
- name: Deploy to server
  env:
    DEPLOY_KEY: ${{ secrets.DEPLOY_SSH_KEY }}
  run: |
    echo "$DEPLOY_KEY" > /tmp/deploy_key
    chmod 600 /tmp/deploy_key
    ssh -i /tmp/deploy_key user@yourserver.com "cd /app && ./deploy.sh"
```

GitHub 会自动在日志中遮蔽 secret 值。如果它出现在输出中，会显示为 `***`。

## 仓库级 secret 与环境级 secret

**仓库级 secret** 对仓库中的所有工作流可用。适用于每个流水线都需要的凭据，比如镜像仓库凭据。

**环境级 secret** 的作用域限定在具名环境（例如 `staging`、`production`）。作业必须声明 `environment: production` 才能访问它们。这样你就可以要求作业在访问生产凭据之前先经过审批：

```yaml
jobs:
  deploy-production:
    environment: production    # can require manual approval in settings
    steps:
      - run: deploy.sh
        env:
          API_KEY: ${{ secrets.PROD_API_KEY }}
```

对于任何涉及生产的操作，使用带必需审批人的环境级 secret 值得多花这点配置功夫。

## 组织级 secret

如果你管理多个仓库，组织级 secret 可以让你在所有仓库（或其中一部分）之间共享凭据，而无需重复设置。在组织级别的 Settings → Secrets 下进行设置。

## 哪些会被遮蔽，哪些不会

如果确切的 secret 值出现在日志中，GitHub 会将其遮蔽。它不会遮蔽派生值——如果你的 secret 是 `abc123`，而你的脚本打印了 `MY_TOKEN=abc123`，它会被遮蔽。但如果脚本把它编码成 base64 再打印出来，就不会被遮蔽。

不要在日志中打印 secret。如果你为了调试而运行了 `set -x`，请在任何使用 secret 的命令之前加上 `set +x`。

## SSH 密钥模式

对于基于 SSH 的部署，常见模式是：

1. 为 CI 生成专用的密钥对：`ssh-keygen -t ed25519 -C "ci-deploy" -f deploy_key`
2. 将**公钥**添加到服务器的 `~/.ssh/authorized_keys` 中
3. 将**私钥**存储为 GitHub Actions secret
4. 在工作流中，将其写入临时文件并用于 SSH

绝不要将你的个人 SSH 密钥复用于 CI。专用密钥可以在不影响你自己访问的情况下进行轮换或吊销。

<!-- ZH_RESOURCES -->
- [GitHub Actions：使用 Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions) -- 类型：参考，时长：10 分钟
- [GitHub Actions：使用 Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment) -- 类型：参考，时长：10 分钟

<!-- ZH_UI -->
1. 在 GitHub Actions secrets 中存储密钥，并在工作流中引用它
2. 理解为什么密钥绝不应出现在日志或 YAML 文件中
3. 了解仓库密钥与环境密钥的区别
4. 密钥已处理完毕。现在如何构建完整流水线？
5. 我已将凭据放在正确位置，但流水线仍只运行测试。我希望整个流程——测试、构建镜像、推送镜像并实际部署——全部在一个自动化流程中完成。
