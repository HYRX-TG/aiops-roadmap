---
id: managing-k8s-manifests
title: Managing Kubernetes Manifests
zone: kubernetes-production
edges:
  to:
    - id: kustomize-basics
      question: >-
        I want a simple way to manage staging and production without duplicating
        YAML.
      detail: >-
        I'm managing two environments and they've already drifted apart because
        I'm copy-pasting YAML and forgetting to update both. I want to define
        things once and only override what's actually different per environment.
    - id: helm-for-cluster-tools
      question: >-
        I need to install things like cert-manager and nginx-ingress. How does
        that work?
      detail: >-
        I can manage my own app manifests, but cert-manager and nginx-ingress
        are third-party software with dozens of resources I don't want to
        maintain by hand. How do people normally install and upgrade these?
difficulty: 1
tags:
  - kubernetes
  - yaml
  - manifests
  - kustomize
  - helm
  - k8s
category: concept
milestones:
  - Understand why copying YAML per environment causes drift
  - Know the difference between Kustomize (patching) and Helm (templating)
  - >-
    Know which tool fits which use case: Kustomize for your apps, Helm for
    community charts
title_zh: "管理 Kubernetes 清单"

---


Raw Kubernetes YAML works fine for one service in one environment. It breaks down the moment you have staging and production, or multiple services, or multiple teams. You end up copy-pasting files, editing them slightly per environment, and slowly losing track of what's running where.

<!-- DEEP_DIVE -->

## The copy-paste drift problem

The naive approach: copy `deployment.yaml` to `deployment-staging.yaml` and `deployment-production.yaml`. Change the image tag, the replica count, the resource limits. Two weeks later, you add an environment variable to staging and forget to add it to production. A month later, the staging config has drifted so far from production that "it works in staging" is meaningless.

The problem isn't discipline — it's that copy-paste YAML has no mechanism to express "this file is staging's version of that file." There's no link. Changes to one don't flow to the other.

## Kustomize: patches on a base

Kustomize takes a different approach: define the base resource once, then define environment-specific overlays that patch only what's different.

```
├── base/
│   ├── deployment.yaml      # replica: 1, image: my-app:latest
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── staging/
    │   └── kustomization.yaml   # patches: replica count, image tag
    └── production/
        └── kustomization.yaml   # patches: higher replicas, limits
```

When you add a new environment variable to base, it's automatically present in both environments. When you change the production replica count, it only touches the production overlay.

Kustomize is built into `kubectl` — `kubectl apply -k overlays/production/` applies the complete rendered manifest.

## Helm: templating and packaging

Helm uses a different model: templates with variables. Instead of YAML patches, you write Go templates with `{{ .Values.image.tag }}`, and provide different values files per environment.

Helm's superpower is packaging: the community distributes Kubernetes software as Helm charts. cert-manager, nginx-ingress, Prometheus, Grafana — all available as charts. You `helm install cert-manager jetstack/cert-manager --version 1.14.0` and get a fully configured, production-ready cert-manager installation with proper RBAC, CRDs, and configuration.

Writing cert-manager manifests by hand would require maintaining dozens of files. Helm handles that for you; you only need to provide the values you want to customize.

## Which tool for which job

**Kustomize for your own applications** — you control the base manifest. Patching is straightforward and explicit. No templating syntax to learn. ArgoCD and Flux both support Kustomize natively.

**Helm for third-party cluster tooling** — you're installing something you didn't write. The chart handles complexity you don't want to think about. Use it for community software.

**Helm for complex applications with logic** — if your manifest generation requires conditionals (install this component if this feature flag is enabled), Helm's templates can express that. Kustomize can't.

The most common production setup: Kustomize overlays for your apps, Helm for cluster infrastructure tools.

## What not to do

Don't commit `helm template` output. It defeats the point of using Helm — the raw YAML loses the upgrade path and values structure.

Don't maintain a single flat directory of YAML files for multiple environments. There's no mechanism to keep them in sync.

Don't use `kubectl apply -f .` on a directory with mixed environment configs. One wrong context and you've applied staging configs to production.

<!-- RESOURCES -->

- [Kustomize Documentation](https://kubectl.docs.kubernetes.io/references/kustomize/) -- type: docs, time: 20m
- [Helm Documentation](https://helm.sh/docs/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
原始 Kubernetes YAML 在单一环境中的单个服务上运行良好。但一旦涉及预发布和生产环境，或者多个服务、多个团队，它就会崩溃。你最终会复制粘贴文件，针对每个环境稍作修改，并逐渐失去对什么在何处运行的追踪。

<!-- ZH_DEEP_DIVE -->
## 复制粘贴漂移问题

朴素的做法是：把 `deployment.yaml` 复制成 `deployment-staging.yaml` 和 `deployment-production.yaml`。修改镜像 tag、副本数、资源限制。两周后，你给 staging 加了一个环境变量，却忘了加到 production。一个月后，staging 配置已经和生产环境偏离太远，以至于“在 staging 上能跑”变得毫无意义。

问题不在于纪律——而在于复制粘贴出来的 YAML 没有任何机制能表达“这个文件是那个文件的 staging 版本”。它们之间没有关联。对其中一个的修改不会流向另一个。

## Kustomize：在 base 上打补丁

Kustomize 采用了不同的思路：只定义一次 base 资源，然后定义针对环境的 overlay，只对差异部分打补丁。

```
├── base/
│   ├── deployment.yaml      # replica: 1, image: my-app:latest
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── staging/
    │   └── kustomization.yaml   # patches: replica count, image tag
    └── production/
        └── kustomization.yaml   # patches: higher replicas, limits
```

当你往 base 里新增一个环境变量时，它会自动出现在两个环境中。当你修改生产环境的副本数时，只会改动生产环境的 overlay。

Kustomize 内置于 `kubectl`——`kubectl apply -k overlays/production/` 会应用完整渲染后的 manifest。

## Helm：模板化与打包

Helm 使用不同的模型：带变量的模板。你不再写 YAML 补丁，而是编写带 `{{ .Values.image.tag }}` 的 Go 模板，并为每个环境提供不同的 values 文件。

Helm 的杀手锏是打包：社区以 Helm chart 的形式分发 Kubernetes 软件。cert-manager、nginx-ingress、Prometheus、Grafana——全都可以作为 chart 获取。执行 `helm install cert-manager jetstack/cert-manager --version 1.14.0`，你就能得到一个完整配置、生产就绪的 cert-manager 安装，包含正确的 RBAC、CRD 和配置。

手写 cert-manager 的 manifest 需要维护几十个文件。Helm 替你处理这些；你只需要提供想要自定义的 values。

## 哪个工具适合哪种场景

**Kustomize 用于你自己的应用**——你掌控 base manifest。打补丁直接且明确。无需学习模板语法。ArgoCD 和 Flux 都原生支持 Kustomize。

**Helm 用于第三方集群工具**——你要安装的不是自己写的东西。chart 处理了你不想操心的复杂性。社区软件就用它。

**Helm 用于带逻辑的复杂应用**——如果你的 manifest 生成需要条件判断（比如某个 feature flag 开启时才安装某个组件），Helm 的模板可以表达这一点。Kustomize 做不到。

最常见的生产环境配置：应用用 Kustomize overlay，集群基础设施工具用 Helm。

## 不要做的事

不要提交 `helm template` 的输出。这违背了使用 Helm 的初衷——原始 YAML 丢失了升级路径和 values 结构。

不要为多个环境维护一个扁平的 YAML 文件目录。没有任何机制能让它们保持同步。

不要对包含混合环境配置的目录执行 `kubectl apply -f .`。一次 context 搞错，你就把 staging 配置应用到了生产环境。

<!-- ZH_RESOURCES -->
- [Kustomize 文档](https://kubectl.docs.kubernetes.io/references/kustomize/) -- 类型：文档，时长：20m
- [Helm 文档](https://helm.sh/docs/) -- 类型：文档，时长：20m

<!-- ZH_UI -->
1. 理解按环境复制 YAML 为何会导致配置漂移
2. 了解 Kustomize（补丁）与 Helm（模板）的区别
3. 了解哪种工具适合哪种场景：Kustomize 用于自己的应用，Helm 用于社区 chart
4. 我想要一种简单的方式来管理预发布和生产环境，而不必重复 YAML。
5. 我在管理两个环境，由于我复制粘贴 YAML 并忘记同步更新两边，它们已经产生了漂移。我想只定义一次，只针对每个环境实际不同的部分做覆盖。
6. 我需要安装 cert-manager 和 nginx-ingress 这类东西。这该怎么操作？
7. 我能管理自己的应用清单，但 cert-manager 和 nginx-ingress 是第三方软件，包含几十个我不想手动维护的资源。人们通常如何安装和升级这些？
