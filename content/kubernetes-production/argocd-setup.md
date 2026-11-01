---
id: argocd-setup
title: Continuous Delivery with ArgoCD
zone: kubernetes-production
edges:
  to:
    - id: k8s-cicd-pipeline
      question: >-
        ArgoCD watches my repo. How does CI feed into this — build, push, and
        trigger a deploy?
      detail: >-
        ArgoCD watches the repo and applies what's there. But CI still needs to
        build the image and update the manifest. I'm not sure how CI and ArgoCD
        are supposed to coordinate — who updates the image tag and when?
    - id: k8s-secrets-management
      question: >-
        ArgoCD is deploying my app — but where do the passwords and API keys
        actually live? They can't be in Git.
      detail: >-
        My app needs database passwords and API keys at runtime. ArgoCD applies
        whatever's in Git, but I can't commit secrets to Git. So where do they
        actually live and how does the pod get them?
difficulty: 3
tags:
  - argocd
  - gitops
  - kubernetes
  - cd
  - k8s
  - deployment
category: tool
milestones:
  - Install ArgoCD in a Kubernetes cluster
  - Connect ArgoCD to a Git repository
  - Create an ArgoCD Application pointing at a Kustomize overlay or Helm chart
  - Trigger a sync and watch ArgoCD reconcile the cluster
  - 'Understand sync policies: manual vs auto-sync'
title_zh: "使用 ArgoCD 进行持续交付"

---


ArgoCD is a Kubernetes controller that watches Git repositories and keeps your cluster synchronized with what's there. You define your desired state in Git — as Kustomize overlays, Helm charts, or plain manifests — and ArgoCD continuously reconciles the cluster to match.

<!-- DEEP_DIVE -->

## Installing ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Or via Helm:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd -n argocd --create-namespace
```

After installation, access the UI by port-forwarding (or exposing via Ingress):

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Get the initial admin password:

```bash
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath="{.data.password}" | base64 -d
```

## The Application CRD

An ArgoCD Application is a CRD that describes what to sync: where the source is and where to apply it.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-api
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/my-org/my-app-manifests
    targetRevision: HEAD
    path: overlays/production          # Kustomize overlay path
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true        # delete resources removed from Git
      selfHeal: true     # revert manual changes to the cluster
```

For Helm:

```yaml
source:
  repoURL: https://charts.jetstack.io
  chart: cert-manager
  targetRevision: v1.14.0
  helm:
    values: |
      replicaCount: 2
```

## Sync policies: manual vs automatic

**Manual sync** — ArgoCD detects drift and shows the app as `OutOfSync` in the UI. A human clicks "Sync" to apply the changes. Good for production if you want a human in the loop for every deployment.

**Automatic sync** — ArgoCD applies changes as soon as they're detected in Git. Combined with `selfHeal: true`, it also reverts manual changes to the cluster. Good for non-production environments or teams comfortable with continuous deployment.

**prune: true** — resources deleted from Git are also deleted from the cluster. Without this, removed resources linger indefinitely. Enable it — otherwise GitOps isn't actually authoritative.

## Sync waves for ordering

Some resources must exist before others. CRDs before the resources that use them. Namespaces before the resources inside them. ArgoCD sync waves handle this:

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"   # apply first
```

Lower wave numbers apply before higher ones. All wave 0 resources must be healthy before wave 1 begins.

## RBAC in ArgoCD

By default, all logged-in users have read-only access. Define policies to control who can sync which applications:

```yaml
# argocd-rbac-cm ConfigMap
data:
  policy.csv: |
    p, role:developers, applications, sync, production/*, deny
    p, role:developers, applications, sync, staging/*, allow
    g, my-team, role:developers
```

Developers can sync staging but not production — production requires a senior engineer or automated promotion.

## The App of Apps pattern

For managing multiple ArgoCD Applications, use the "App of Apps" pattern: one ArgoCD Application whose source is a directory of Application manifests. ArgoCD deploys the Application manifests, which then bootstrap all the other applications. Your entire cluster state is expressed as Applications in Git.

<!-- RESOURCES -->

- [ArgoCD Getting Started](https://argo-cd.readthedocs.io/en/stable/getting_started/) -- type: docs, time: 30m
- [ArgoCD Application CRD Reference](https://argo-cd.readthedocs.io/en/stable/operator-manual/application.yaml/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
ArgoCD 是一个 Kubernetes 控制器，它监视 Git 仓库，并使集群与仓库中的内容保持同步。你在 Git 中定义期望状态——可以是 Kustomize overlay、Helm chart 或纯 manifest——ArgoCD 会持续协调集群以与之匹配。

<!-- ZH_DEEP_DIVE -->
## 安装 ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

或通过 Helm 安装：

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd -n argocd --create-namespace
```

安装完成后，通过端口转发（或通过 Ingress 暴露）访问 UI：

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

获取初始 admin 密码：

```bash
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath="{.data.password}" | base64 -d
```

## Application CRD

ArgoCD Application 是一个 CRD，用于描述要同步的内容：源在哪里，以及应用到何处。

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-api
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/my-org/my-app-manifests
    targetRevision: HEAD
    path: overlays/production          # Kustomize overlay path
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true        # delete resources removed from Git
      selfHeal: true     # revert manual changes to the cluster
```

对于 Helm：

```yaml
source:
  repoURL: https://charts.jetstack.io
  chart: cert-manager
  targetRevision: v1.14.0
  helm:
    values: |
      replicaCount: 2
```

## 同步策略：手动与自动

**手动同步** — ArgoCD 检测到漂移后，会在 UI 中将应用显示为 `OutOfSync`。由人工点击“Sync”来应用变更。如果你希望每次部署都有人工介入，这适合生产环境。

**自动同步** — ArgoCD 一旦在 Git 中检测到变更就立即应用。结合 `selfHeal: true`，它还会还原对集群的手动更改。适合非生产环境，或已习惯持续部署的团队。

**prune: true** — 从 Git 中删除的资源也会从集群中删除。若不启用，被移除的资源会无限期残留。请启用它——否则 GitOps 实际上并不具备权威性。

## 用于排序的同步波次

某些资源必须先于其他资源存在。CRD 先于使用它们的资源。Namespace 先于其中的资源。ArgoCD 同步波次可处理这一点：

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"   # apply first
```

波次编号较小的先应用。所有波次 0 的资源必须健康后，波次 1 才会开始。

## ArgoCD 中的 RBAC

默认情况下，所有已登录用户都具有只读访问权限。定义策略来控制谁可以同步哪些应用：

```yaml
# argocd-rbac-cm ConfigMap
data:
  policy.csv: |
    p, role:developers, applications, sync, production/*, deny
    p, role:developers, applications, sync, staging/*, allow
    g, my-team, role:developers
```

开发者可以同步 staging，但不能同步 production——production 需要高级工程师或自动化晋升。

## App of Apps 模式

要管理多个 ArgoCD Application，可使用“App of Apps”模式：一个 ArgoCD Application，其源是一个包含 Application 清单的目录。ArgoCD 部署这些 Application 清单，进而引导所有其他应用。你的整个集群状态都以 Git 中的 Application 形式表达。

<!-- ZH_RESOURCES -->
- [ArgoCD 入门](https://argo-cd.readthedocs.io/en/stable/getting_started/) -- 类型：文档，时长：30 分钟
- [ArgoCD Application CRD 参考](https://argo-cd.readthedocs.io/en/stable/operator-manual/application.yaml/) -- 类型：文档，时长：15 分钟

<!-- ZH_UI -->
1. 在 Kubernetes 集群中安装 ArgoCD
2. 将 ArgoCD 连接到 Git 仓库
3. 创建一个指向 Kustomize overlay 或 Helm chart 的 ArgoCD Application
4. 触发同步并观察 ArgoCD 协调集群状态
5. 理解同步策略：手动同步与自动同步
6. ArgoCD 会监视我的仓库。CI 如何融入这一流程——构建、推送并触发部署？
7. ArgoCD 监视仓库并应用其中的内容。但 CI 仍然需要构建镜像并更新 manifest。我不确定 CI 和 ArgoCD 应该如何协调——谁来更新镜像 tag，以及何时更新？
8. ArgoCD 正在部署我的应用——但密码和 API key 实际存放在哪里？它们不能放在 Git 里。
9. 我的应用在运行时需要数据库密码和 API key。ArgoCD 会应用 Git 中的内容，但我不能把 secret 提交到 Git。那么它们实际存放在哪里，Pod 又是如何获取它们的？
