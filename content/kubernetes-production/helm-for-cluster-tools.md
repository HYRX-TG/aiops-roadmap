---
id: helm-for-cluster-tools
title: Helm for Cluster Tooling
zone: kubernetes-production
edges:
  to:
    - id: gitops-intro
      question: >-
        I can install cluster tools with Helm. How do I manage all of this with
        GitOps?
      detail: >-
        I've been running helm install manually whenever I set up a cluster. But
        I want cluster tooling to be reproducible and tracked in Git like
        everything else — not something I install by hand and forget about.
difficulty: 2
tags:
  - kubernetes
  - helm
  - cert-manager
  - nginx
  - cluster-tools
  - k8s
  - charts
category: tool
milestones:
  - 'Install a community chart (cert-manager, nginx-ingress, or similar)'
  - Understand what a Helm release is and how to inspect it
  - Override chart values with a values.yaml file
  - Upgrade and rollback a Helm release
  - Understand why Helm is the standard for distributing community K8s software
title_zh: "Helm 用于集群工具"

---


Helm is how the Kubernetes community distributes software. cert-manager, nginx-ingress, Prometheus, ArgoCD, Grafana — all available as Helm charts. Instead of maintaining dozens of YAML files for a third-party tool, you install a chart, customize it with a values file, and let Helm manage it from there.

<!-- DEEP_DIVE -->

## What a Helm chart is

A Helm chart is a packaged Kubernetes application: Go templates, default values, CRD definitions, RBAC, and all the resources needed to run the software. When you `helm install`, Helm renders the templates with your values and applies the resulting YAML to the cluster.

A Helm release is an instance of a chart running in your cluster. You can have multiple releases of the same chart (two nginx-ingress controllers for different use cases, for example).

## Installing a chart

```bash
# Add the chart repository
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.14.0 \
  --set crds.enabled=true
```

Pin the version. Using `--version` ensures you know exactly what you're running. Omitting it gives you whatever's latest — which changes when you reinstall.

## Customizing with values

Helm charts expose configuration through a values file. Override the defaults you care about:

```yaml
# cert-manager-values.yaml
replicaCount: 2
resources:
  requests:
    cpu: 100m
    memory: 128Mi

prometheus:
  enabled: true
  servicemonitor:
    enabled: true
```

```bash
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  -f cert-manager-values.yaml \
  --version v1.14.0
```

Always read the chart's default `values.yaml` before installing. It documents every knob available.

## Inspecting and upgrading a release

```bash
# List releases
helm list -A

# See what values a release is using
helm get values cert-manager -n cert-manager

# Upgrade to a new version
helm upgrade cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  -f cert-manager-values.yaml \
  --version v1.15.0

# Roll back if the upgrade broke something
helm rollback cert-manager 1 -n cert-manager
```

## Don't put secrets in values

Helm values files end up in the cluster as a ConfigMap (readable by anyone with access). Never put passwords, API keys, or tokens in a values file. Use External Secrets Operator or Sealed Secrets for secrets that Helm-managed charts need.

## Storing values in Git (the GitOps pattern)

Your values files belong in Git, versioned and reviewable:

```
cluster/
├── cert-manager/
│   ├── values.yaml
│   └── namespace.yaml
└── nginx-ingress/
    └── values.yaml
```

If you're using ArgoCD, create an Application for each Helm release. ArgoCD will reconcile the Helm release from Git, including when you upgrade the chart version by editing the Application's `targetRevision`.

This is the right production pattern: no one runs `helm install` on a laptop. Changes go through Git and are applied by the GitOps operator.

<!-- RESOURCES -->

- [Helm Documentation](https://helm.sh/docs/) -- type: docs, time: 25m
- [Helm Hub / Artifact Hub](https://artifacthub.io/) -- type: tool, time: 10m

<!-- ZH_SUMMARY -->
Helm 是 Kubernetes 社区分发软件的方式。cert-manager、nginx-ingress、Prometheus、ArgoCD、Grafana——都可以通过 Helm chart 获取。你无需为第三方工具维护数十个 YAML 文件，只需安装一个 chart，用 values 文件进行定制，之后交由 Helm 管理即可。

<!-- ZH_DEEP_DIVE -->
## 什么是 Helm chart

Helm chart 是一个打包好的 Kubernetes 应用：包含 Go 模板、默认值、CRD 定义、RBAC，以及运行该软件所需的全部资源。执行 `helm install` 时，Helm 会用你提供的 values 渲染模板，并把生成的 YAML 应用到集群。

Helm release 是某个 chart 在集群中运行的一个实例。同一个 chart 可以有多个 release（例如为不同使用场景部署两个 nginx-ingress controller）。

## 安装 chart

```bash
# Add the chart repository
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.14.0 \
  --set crds.enabled=true
```

固定版本。使用 `--version` 可以确保你清楚自己运行的到底是什么版本。省略它就会拿到最新的版本——而最新版本在你重新安装时会发生变化。

## 通过 values 自定义

Helm chart 通过 values 文件暴露配置。覆盖你关心的默认值：

```yaml
# cert-manager-values.yaml
replicaCount: 2
resources:
  requests:
    cpu: 100m
    memory: 128Mi

prometheus:
  enabled: true
  servicemonitor:
    enabled: true
```

```bash
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  -f cert-manager-values.yaml \
  --version v1.14.0
```

安装前务必阅读 chart 的默认 `values.yaml`。它记录了所有可配置项。

## 查看与升级 release

```bash
# List releases
helm list -A

# See what values a release is using
helm get values cert-manager -n cert-manager

# Upgrade to a new version
helm upgrade cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  -f cert-manager-values.yaml \
  --version v1.15.0

# Roll back if the upgrade broke something
helm rollback cert-manager 1 -n cert-manager
```

## 不要把密钥放进 values

Helm values 文件最终会以 ConfigMap 的形式存在于集群中（任何有访问权限的人都能读取）。绝不要把密码、API key 或 token 放进 values 文件。对于由 Helm 管理的 chart 所需的密钥，请使用 External Secrets Operator 或 Sealed Secrets。

## 把 values 存入 Git（GitOps 模式）

你的 values 文件应当纳入 Git，进行版本管理并可审查：

```
cluster/
├── cert-manager/
│   ├── values.yaml
│   └── namespace.yaml
└── nginx-ingress/
    └── values.yaml
```

如果你使用 ArgoCD，请为每个 Helm release 创建一个 Application。ArgoCD 会从 Git 协调 Helm release，包括你通过编辑 Application 的 `targetRevision` 来升级 chart 版本时。

这才是正确的生产模式：没有人在笔记本上运行 `helm install`。变更通过 Git 流转，并由 GitOps operator 应用。

<!-- ZH_RESOURCES -->
- [Helm 文档](https://helm.sh/docs/) -- 类型：文档，时长：25 分钟
- [Helm Hub / Artifact Hub](https://artifacthub.io/) -- 类型：工具，时长：10 分钟

<!-- ZH_UI -->
1. 安装一个社区 chart（cert-manager、nginx-ingress 或类似）
2. 理解什么是 Helm release 以及如何检查它
3. 使用 values.yaml 文件覆盖 chart 值
4. 升级和回滚 Helm release
5. 理解为什么 Helm 是分发社区 K8s 软件的标准
6. 我可以用 Helm 安装集群工具。如何用 GitOps 管理这一切？
7. 每次搭建集群时我都是手动运行 helm install。但我希望集群工具像其他东西一样可复现并纳入 Git 跟踪——而不是装完就忘的手动操作。
