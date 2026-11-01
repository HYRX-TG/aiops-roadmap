---
id: kustomize-basics
title: Managing Your App with Kustomize
zone: kubernetes-production
edges:
  to:
    - id: gitops-intro
      question: Kustomize handles my manifests. How do I stop applying them by hand?
      detail: >-
        I've got Kustomize overlays for staging and production, but I'm still
        running kubectl apply -k manually after every change. I want something
        watching the repo and doing that automatically.
difficulty: 2
tags:
  - kubernetes
  - kustomize
  - manifests
  - overlays
  - environments
  - k8s
category: practice
milestones:
  - Understand the base + overlays pattern
  - Write a kustomization.yaml that patches a base manifest for staging
  - Apply a Kustomize overlay with kubectl apply -k
  - >-
    Use patches to change replica counts, image tags, and env vars per
    environment
  - Understand how ArgoCD consumes Kustomize overlays natively
title_zh: "使用 Kustomize 管理你的应用"

---


Kustomize lets you define your Kubernetes resources once in a base, then layer environment-specific changes on top using overlays. No templating language — just patches. The same base feeds staging and production; overlays express only what's different.

<!-- DEEP_DIVE -->

## The base + overlays structure

```
my-app/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── staging/
    │   ├── kustomization.yaml
    │   └── replica-patch.yaml
    └── production/
        ├── kustomization.yaml
        └── production-patch.yaml
```

The base contains complete, valid Kubernetes manifests. The overlays reference the base and add patches. Running `kubectl apply -k overlays/production/` renders the base with the production patches applied and applies it all at once.

## The kustomization.yaml

The base `kustomization.yaml` lists the resources:

```yaml
# base/kustomization.yaml
resources:
  - deployment.yaml
  - service.yaml
```

An overlay `kustomization.yaml` references the base and adds patches:

```yaml
# overlays/production/kustomization.yaml
resources:
  - ../../base

patches:
  - path: production-patch.yaml

images:
  - name: my-app
    newTag: "v1.4.2"
```

The `images` field updates the container image tag without touching the deployment YAML.

## Common patches

**Changing replica count:**

```yaml
# overlays/production/replica-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5
```

**Changing resource limits:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
        - name: app
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: "2"
              memory: 1Gi
```

**Adding environment variables:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
        - name: app
          env:
            - name: APP_ENV
              value: production
```

Patches are strategic merges — they merge into the base resource rather than replacing it. You only need to specify the fields you want to change.

## Applying a Kustomize overlay

```bash
# Preview what will be applied (renders the final YAML without applying)
kubectl kustomize overlays/production/

# Apply it
kubectl apply -k overlays/production/

# ArgoCD uses the same kustomize rendering internally
```

## How ArgoCD uses Kustomize

ArgoCD has native Kustomize support. When you create an Application pointing at a Kustomize overlay directory, ArgoCD runs `kustomize build` internally and applies the result. You don't need to run anything manually — ArgoCD handles it on every sync.

```yaml
# ArgoCD Application pointing at a Kustomize overlay
spec:
  source:
    repoURL: https://github.com/my-org/my-app-manifests
    targetRevision: HEAD
    path: overlays/production
```

## When Kustomize isn't enough

Kustomize has no conditionals or loops. If you need to conditionally include a resource (deploy this sidecar only in production, not staging), Kustomize can't express that cleanly. You'd either duplicate resources across overlays or switch to Helm.

For most application deployments, Kustomize is sufficient. When you find yourself fighting the patch model, that's the signal to consider Helm.

<!-- RESOURCES -->

- [Kustomize Documentation](https://kubectl.docs.kubernetes.io/references/kustomize/) -- type: docs, time: 20m
- [Kustomize Examples](https://github.com/kubernetes-sigs/kustomize/tree/master/examples) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
Kustomize 让你在 base 中定义一次 Kubernetes 资源，然后通过 overlay 在其上叠加环境特定的变更。无需模板语言——只需 patch。同一个 base 供给 staging 和 production；overlay 只表达差异部分。

<!-- ZH_DEEP_DIVE -->
## base + overlays 结构

```
my-app/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── staging/
    │   ├── kustomization.yaml
    │   └── replica-patch.yaml
    └── production/
        ├── kustomization.yaml
        └── production-patch.yaml
```

base 包含完整、有效的 Kubernetes 清单。overlays 引用 base 并添加补丁。运行 `kubectl apply -k overlays/production/` 会渲染出应用了 production 补丁的 base，并一次性全部应用。

## kustomization.yaml

base 的 `kustomization.yaml` 列出资源：

```yaml
# base/kustomization.yaml
resources:
  - deployment.yaml
  - service.yaml
```

overlay 的 `kustomization.yaml` 引用 base 并添加补丁：

```yaml
# overlays/production/kustomization.yaml
resources:
  - ../../base

patches:
  - path: production-patch.yaml

images:
  - name: my-app
    newTag: "v1.4.2"
```

`images` 字段会更新容器镜像标签，而无需改动 deployment YAML。

## 常见补丁

**修改副本数：**

```yaml
# overlays/production/replica-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5
```

**修改资源限制：**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
        - name: app
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: "2"
              memory: 1Gi
```

**添加环境变量：**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
        - name: app
          env:
            - name: APP_ENV
              value: production
```

补丁是策略性合并——它们会合并到 base 资源中，而不是替换它。你只需指定想要更改的字段。

## 应用 Kustomize overlay

```bash
# Preview what will be applied (renders the final YAML without applying)
kubectl kustomize overlays/production/

# Apply it
kubectl apply -k overlays/production/

# ArgoCD uses the same kustomize rendering internally
```

## ArgoCD 如何使用 Kustomize

ArgoCD 原生支持 Kustomize。当你创建一个指向 Kustomize overlay 目录的 Application 时，ArgoCD 会在内部运行 `kustomize build` 并应用结果。你无需手动运行任何命令——ArgoCD 会在每次同步时处理。

```yaml
# ArgoCD Application pointing at a Kustomize overlay
spec:
  source:
    repoURL: https://github.com/my-org/my-app-manifests
    targetRevision: HEAD
    path: overlays/production
```

## 当 Kustomize 不够用时

Kustomize 没有条件判断或循环。如果你需要有条件地包含某个资源（仅在 production 中部署此 sidecar，而不在 staging 中），Kustomize 无法清晰地表达这一点。你要么在多个 overlay 中重复资源，要么改用 Helm。

对于大多数应用部署，Kustomize 已经足够。当你发现自己与补丁模型较劲时，那就是考虑 Helm 的信号。

<!-- ZH_RESOURCES -->
- [Kustomize 文档](https://kubectl.docs.kubernetes.io/references/kustomize/) -- 类型：文档，时长：20m
- [Kustomize 示例](https://github.com/kubernetes-sigs/kustomize/tree/master/examples) -- 类型：文档，时长：20m

<!-- ZH_UI -->
1. 理解 base + overlays 模式
2. 编写 kustomization.yaml，为 staging 环境对 base 清单打补丁
3. 使用 kubectl apply -k 应用 Kustomize overlay
4. 使用 patches 按环境修改副本数、镜像标签和环境变量
5. 理解 ArgoCD 如何原生消费 Kustomize overlay
6. Kustomize 负责处理我的清单。如何不再手动应用它们？
7. 我已经为 staging 和 production 准备了 Kustomize overlay，但每次变更后仍在手动运行 kubectl apply -k。我想要有东西监视仓库并自动执行该操作。
