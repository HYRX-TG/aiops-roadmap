---
id: gitops-intro
title: 'GitOps: Git as the Source of Truth'
zone: kubernetes-production
edges:
  to:
    - id: argocd-setup
      question: >-
        My manifests are in Git — how do I make the cluster automatically apply
        them when I merge?
      detail: >-
        I've been running kubectl apply by hand after every change, which is
        error-prone and means I could forget a step. I want merging a PR to be
        what actually triggers the deployment — but I'm not sure what's doing
        the watching and applying.
difficulty: 2
tags:
  - gitops
  - kubernetes
  - argocd
  - flux
  - deployment
  - k8s
category: concept
milestones:
  - >-
    Understand the GitOps model: Git is the desired state, the operator
    reconciles
  - Know the difference between push-based and pull-based deployments
  - Understand why GitOps gives you a free audit trail and rollback path
title_zh: "GitOps：以 Git 作为唯一可信源"

---


GitOps is a deployment model where Git is the single source of truth for cluster state. Instead of CI pushing changes directly to the cluster, a controller inside the cluster watches a Git repository and reconciles the cluster to match what's there. The cluster pulls from Git — it's never pushed to.

<!-- DEEP_DIVE -->

## Push-based vs pull-based deployments

**Push-based (traditional CI/CD):** Your CI pipeline runs `kubectl apply` or `helm upgrade` at the end of a build. The cluster accepts changes from external systems. The pipeline needs credentials to write to the cluster. The cluster's actual state may drift from what was last deployed — there's nothing continuously reconciling.

**Pull-based (GitOps):** A controller (ArgoCD, Flux) runs inside the cluster. It watches a Git repository. When the repository changes, the controller applies the changes. The controller continuously reconciles actual state with desired state — if someone manually edits a resource in the cluster, the controller reverts it to match Git.

The key advantage of pull-based: CI doesn't need cluster credentials. You don't have to trust every CI pipeline with write access to production.

## What GitOps gives you

**Audit trail** — every deployment is a Git commit. Who deployed what, when, and why is recorded in commit history. This is invaluable during an incident.

**Free rollback** — rolling back is `git revert`. The GitOps controller sees the revert commit and rolls the cluster back to the previous state. No special rollback commands; Git history is your deployment history.

**Drift detection** — if someone manually changes something in the cluster (emergency hotfix, configuration tweak), the GitOps controller detects the drift and alerts you — or automatically reverts it, depending on your sync policy.

**Reproducibility** — a new cluster can be bootstrapped from Git. Your cluster state is defined in code, not reconstructed from memory.

## The split between CI and CD

In a GitOps model, CI and CD are separate concerns:

**CI (Continuous Integration):** Build and test the code. Build and push a container image. Update the image tag in the Git repository (in the manifests repo).

**CD (Continuous Deployment / GitOps):** The controller watches the repository. When the image tag changes, it applies the new manifest. The cluster updates.

CI doesn't touch the cluster. CD doesn't build images. They communicate through Git.

## Flux vs ArgoCD

Both are pull-based GitOps operators. Both watch Git repositories and reconcile cluster state.

**ArgoCD** — has a web UI for visualizing application state, sync status, and resource health. More feature-rich. Has its own RBAC model. The most widely adopted option.

**Flux** — more Kubernetes-native (everything is a CRD). No built-in UI. More composable. Good fit for teams that prefer CLI and want less opinion.

For most teams starting out, ArgoCD is easier to reason about and has better visibility. Flux is preferred by teams that want a more minimal, CLI-centric workflow.

<!-- RESOURCES -->

- [OpenGitOps Principles](https://opengitops.dev/) -- type: docs, time: 10m
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/en/stable/) -- type: docs, time: 20m
- [Flux Documentation](https://fluxcd.io/flux/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
GitOps 是一种部署模型，其中 Git 是集群状态的唯一事实来源。CI 不再直接将变更推送到集群，而是由集群内的控制器监视 Git 仓库，并将集群协调至与仓库中的状态一致。集群从 Git 拉取——永远不会被推送。

<!-- ZH_DEEP_DIVE -->
## 基于推送与基于拉取的部署

**基于推送（传统 CI/CD）：** 你的 CI 流水线在构建结束时运行 `kubectl apply` 或 `helm upgrade`。集群接受来自外部系统的变更。流水线需要凭据才能写入集群。集群的实际状态可能与最后一次部署的状态发生漂移——没有任何机制持续进行协调。

**基于拉取（GitOps）：** 一个控制器（ArgoCD、Flux）运行在集群内部。它监视一个 Git 仓库。当仓库发生变化时，控制器应用这些变更。控制器持续将实际状态与期望状态进行协调——如果有人手动编辑了集群中的某个资源，控制器会将其还原以匹配 Git。

基于拉取的关键优势：CI 不需要集群凭据。你不必信任每个 CI 流水线都拥有对生产环境的写入权限。

## GitOps 为你带来的好处

**审计追踪** —— 每次部署都是一次 Git 提交。谁在何时部署了什么、为什么部署，都记录在提交历史中。这在事故处理期间价值无可估量。

**免费的回滚** —— 回滚就是 `git revert`。GitOps 控制器看到回滚提交后，会将集群回滚到之前的状态。无需特殊的回滚命令；Git 历史就是你的部署历史。

**漂移检测** —— 如果有人手动更改了集群中的某些内容（紧急热修复、配置调整），GitOps 控制器会检测到漂移并提醒你——或者根据你的同步策略自动还原。

**可复现性** —— 新集群可以从 Git 引导启动。你的集群状态定义在代码中，而不是凭记忆重建。

## CI 与 CD 的分离

在 GitOps 模型中，CI 和 CD 是相互独立的关注点：

**CI（持续集成）：** 构建并测试代码。构建并推送容器镜像。更新 Git 仓库（清单仓库）中的镜像标签。

**CD（持续部署 / GitOps）：** 控制器监视仓库。当镜像标签变化时，它应用新的清单。集群随之更新。

CI 不接触集群。CD 不构建镜像。它们通过 Git 进行通信。

## Flux 与 ArgoCD

两者都是基于拉取的 GitOps 运算符。两者都监视 Git 仓库并协调集群状态。

**ArgoCD** —— 提供 Web UI，用于可视化应用状态、同步状态和资源健康度。功能更丰富。拥有自己的 RBAC 模型。是采用最广泛的选项。

**Flux** —— 更 Kubernetes 原生（一切都是 CRD）。没有内置 UI。更具可组合性。适合偏好 CLI 且希望更少预设的团队。

对于大多数刚起步的团队来说，ArgoCD 更容易理解，可见性也更好。Flux 则受到希望采用更精简、以 CLI 为中心的工作流的团队青睐。

<!-- ZH_RESOURCES -->
- [OpenGitOps 原则](https://opengitops.dev/) -- type: docs, time: 10m
- [ArgoCD 文档](https://argo-cd.readthedocs.io/en/stable/) -- type: docs, time: 20m
- [Flux 文档](https://fluxcd.io/flux/) -- type: docs, time: 20m

<!-- ZH_UI -->
1. 理解 GitOps 模型：Git 是期望状态，operator 负责协调
2. 了解基于推送和基于拉取的部署之间的区别
3. 理解为什么 GitOps 能提供免费的审计轨迹和回滚路径
4. 我的清单在 Git 中——合并时如何让集群自动应用它们？
5. 每次变更后我一直在手动运行 kubectl apply，这容易出错，而且可能忘记某个步骤。我希望合并 PR 成为真正触发部署的动作——但我不确定是什么在监视并应用。
