---
id: k8s-cicd-pipeline
title: CI/CD Pipeline for Kubernetes
zone: kubernetes-production
edges:
  to:
    - id: multi-env-k8s
      question: >-
        The pipeline works for one environment. How do I promote between staging
        and production?
      detail: >-
        Right now everything that merges to main goes straight to production. I
        want to deploy to staging first, verify it works, and then promote
        deliberately — not push to prod automatically on every commit.
difficulty: 3
tags:
  - ci-cd
  - kubernetes
  - gitops
  - argocd
  - github-actions
  - containers
  - k8s
category: practice
milestones:
  - Build and push a container image on every commit to main
  - Update the image tag in the Helm values file (or Kustomize overlay) via CI
  - Have ArgoCD pick up the change and deploy it automatically
  - >-
    Understand the full loop: commit → build → push → update manifest → ArgoCD
    syncs
title_zh: "用于 Kubernetes 的 CI/CD 流水线"

---


In a GitOps model, CI and CD have distinct, non-overlapping responsibilities. CI builds, tests, and publishes the container image. CD (ArgoCD or Flux) watches the manifest repository and applies changes. They communicate through Git — CI never touches the cluster directly.

<!-- DEEP_DIVE -->

## The full pipeline

```
Code commit → CI builds & tests → CI pushes image to registry
→ CI updates image tag in manifest repo → ArgoCD detects change
→ ArgoCD syncs cluster → new pods running
```

The manifest repository is separate from the application code repository. This is the key structure that makes GitOps work: you can see the history of what was deployed and when, independent of application code changes.

## The CI side: build and update

A GitHub Actions workflow for the CI half:

```yaml
name: Build and Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push image
        run: |
          docker build -t ghcr.io/my-org/my-app:${{ github.sha }} .
          docker push ghcr.io/my-org/my-app:${{ github.sha }}

      - name: Update image tag in manifests
        run: |
          git clone https://github.com/my-org/my-app-manifests
          cd my-app-manifests
          # Update the image tag in the Kustomize overlay
          kustomize edit set image my-app=ghcr.io/my-org/my-app:${{ github.sha }} \
            --stack-trace
          git config user.email "ci@example.com"
          git config user.name "CI Bot"
          git add -A
          git commit -m "Update my-app image to ${{ github.sha }}"
          git push
```

Use the git commit SHA as the image tag — not `latest`. Tags like `latest` are mutable and create ambiguity about what's actually deployed.

## Updating image tags

Three common approaches:

**kustomize edit set image** — works if your overlay uses Kustomize. Updates the image field in `kustomization.yaml` directly.

**yq / sed** — directly edit the image field in a values file or manifest. Simple but fragile if the format changes.

**Helm values update** — if using Helm in ArgoCD, update the `image.tag` in your values file committed to Git.

## Environment separation in the pipeline

Don't deploy to production on every main branch commit. The pattern:

1. Every commit to `main` → deploy to staging automatically
2. Promote to production by opening a PR that updates the production image tag
3. Require review and approval before merging
4. Merging triggers ArgoCD sync to production

This gives you: automatic staging deployment, human gate before production, and a Git record of every production deployment (the promotion PR).

## What not to do

**Don't `kubectl apply` from CI directly.** CI pipelines shouldn't have cluster credentials. If CI is compromised, the blast radius should be limited to the image registry and manifest repo — not direct cluster access.

**Don't use `latest` tags.** You lose the ability to audit what's deployed, and you can't reliably roll back.

**Don't have CI wait for the deployment to complete.** CI's job ends when it pushes the manifest change. ArgoCD's job is reconciling the cluster. These are separate systems on separate timelines.

## Image signing and attestation (optional)

For higher-security environments, consider signing images with Sigstore/cosign and using OPA or Kyverno to reject unsigned images in production. This prevents an attacker who compromises your registry from deploying arbitrary code.

<!-- RESOURCES -->

- [ArgoCD CI Integration](https://argo-cd.readthedocs.io/en/stable/operator-manual/ci_automation/) -- type: docs, time: 15m
- [GitHub Actions Documentation](https://docs.github.com/en/actions) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
在 GitOps 模型中，CI 和 CD 具有各自独立、互不重叠的职责。CI 负责构建、测试并发布容器镜像。CD（ArgoCD 或 Flux）负责监视清单仓库并应用变更。二者通过 Git 进行通信——CI 从不直接接触集群。

<!-- ZH_DEEP_DIVE -->
## 完整流水线

```
代码提交 → CI 构建与测试 → CI 推送镜像到镜像仓库
→ CI 更新 manifest 仓库中的镜像 tag → ArgoCD 检测到变更
→ ArgoCD 同步集群 → 新 Pod 运行
```

manifest 仓库与应用代码仓库是分离的。这正是 GitOps 得以运作的关键结构：你可以独立于应用代码变更，查看部署了什么以及何时部署的历史记录。

## CI 侧：构建与更新

CI 部分的 GitHub Actions workflow：

```yaml
name: Build and Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push image
        run: |
          docker build -t ghcr.io/my-org/my-app:${{ github.sha }} .
          docker push ghcr.io/my-org/my-app:${{ github.sha }}

      - name: Update image tag in manifests
        run: |
          git clone https://github.com/my-org/my-app-manifests
          cd my-app-manifests
          # Update the image tag in the Kustomize overlay
          kustomize edit set image my-app=ghcr.io/my-org/my-app:${{ github.sha }} \
            --stack-trace
          git config user.email "ci@example.com"
          git config user.name "CI Bot"
          git add -A
          git commit -m "Update my-app image to ${{ github.sha }}"
          git push
```

使用 git commit SHA 作为镜像 tag——不要用 `latest`。像 `latest` 这样的 tag 是可变的，会对实际部署的内容造成歧义。

## 更新镜像 tag

三种常见方式：

**kustomize edit set image** —— 如果你的 overlay 使用 Kustomize，则适用。直接更新 `kustomization.yaml` 中的 image 字段。

**yq / sed** —— 直接编辑 values 文件或 manifest 中的 image 字段。简单，但格式变化时容易失效。

**Helm values 更新** —— 如果在 ArgoCD 中使用 Helm，更新提交到 Git 的 values 文件中的 `image.tag`。

## 流水线中的环境隔离

不要每次 main 分支提交都部署到生产环境。模式如下：

1. 每次提交到 `main` → 自动部署到 staging
2. 通过提交更新生产镜像 tag 的 PR 来晋升到生产
3. 合并前要求 review 和审批
4. 合并触发 ArgoCD 同步到生产

这样你获得：自动的 staging 部署、生产前的人工卡点，以及每次生产部署的 Git 记录（晋升 PR）。

## 不要做的事

**不要从 CI 直接 `kubectl apply`。** CI 流水线不应持有集群凭证。如果 CI 被攻破，影响范围应限制在镜像仓库和 manifest 仓库——而不是直接的集群访问。

**不要使用 `latest` tag。** 你会失去审计实际部署内容的能力，也无法可靠地回滚。

**不要让 CI 等待部署完成。** CI 的工作在推送 manifest 变更后就结束了。ArgoCD 的工作是协调集群。这是两个独立的系统，运行在各自的时间线上。

## 镜像签名与证明（可选）

对于安全性要求更高的环境，考虑使用 Sigstore/cosign 对镜像签名，并使用 OPA 或 Kyverno 在生产环境中拒绝未签名的镜像。这可以防止攻破镜像仓库的攻击者部署任意代码。

<!-- ZH_RESOURCES -->
- [ArgoCD CI 集成](https://argo-cd.readthedocs.io/en/stable/operator-manual/ci_automation/) -- 类型: 文档, 时长: 15m
- [GitHub Actions 文档](https://docs.github.com/en/actions) -- 类型: 文档, 时长: 20m

<!-- ZH_UI -->
1. 每次提交到 main 分支时构建并推送容器镜像
2. 通过 CI 更新 Helm values 文件（或 Kustomize overlay）中的镜像标签
3. 让 ArgoCD 检测到变更并自动部署
4. 理解完整闭环：提交 → 构建 → 推送 → 更新清单 → ArgoCD 同步
5. 流水线目前只适用于一个环境。如何在 staging 和 production 之间做晋升？
6. 目前所有合并到 main 的变更都会直接进入生产环境。我希望先部署到 staging，验证可用后再有意识地晋升——而不是每次提交都自动推送到生产。
