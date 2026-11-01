---
id: multi-env-k8s
title: Multi-Environment Promotion
zone: kubernetes-production
edges:
  to:
    - id: resource-requests-limits
      question: >-
        My app is deployed across environments — but how do I make sure it
        doesn't starve or take down other pods?
      detail: >-
        In staging I don't care much about resource usage. But in production I
        worry that one misbehaving pod could consume all the memory and take
        everything else down with it. How do I actually prevent that?
    - id: service-mesh-problems
      question: >-
        Everything is running. But how do services talk to each other securely,
        and how do I know what's going wrong?
      detail: >-
        My services communicate over plain HTTP inside the cluster. I've heard
        that's not great from a security standpoint. And when a request fails
        somewhere in the chain, I have no visibility into which service is
        responsible.
    - id: namespace-strategy
      question: >-
        Should I use separate namespaces or separate clusters for each
        environment?
      detail: >-
        I've been using namespaces to separate staging and production but I'm
        not sure that's actually providing real isolation. What's actually
        stopping a misconfigured staging pod from hitting the production
        database?
    - id: network-policies
      question: >-
        How do I stop services in one environment from accidentally talking to
        services in another?
      detail: >-
        Staging and production are in the same cluster. I keep worrying that a
        misconfigured service in staging could accidentally call the production
        API or database. Right now there's nothing at the network level stopping
        that from happening.
difficulty: 3
tags:
  - kubernetes
  - environments
  - staging
  - production
  - gitops
  - promotion
  - k8s
category: practice
milestones:
  - Separate staging and production into distinct namespaces or clusters
  - Promote a release from staging to production via a pull request
  - >-
    Understand environment-specific config using Helm values or Kustomize
    overlays
  - Require manual approval before production deployments
title_zh: "多环境发布"

---


Staging exists to catch problems before they reach production. But a staging environment only provides value if it closely resembles production and promotion between them is deliberate — not automatic, not accidental.

<!-- DEEP_DIVE -->

## What each environment is for

**Development** — fast iteration, loose stability requirements. Developers need frequent deploys; breaking changes are acceptable. Can be namespaces in a shared cluster.

**Staging** — production-like. Same Kubernetes version, same resource limits, same networking. The bar is: "would this break in production?" Integration tests, load tests, and manual QA happen here.

**Production** — the real thing. Changes are deliberate. Deploys require approval. Rollbacks are practiced, not improvised.

Running staging on a small, cheap cluster with half the resources of production is a mistake. You'll find resource-related bugs in production that staging never surfaced.

## Namespace-per-environment vs cluster-per-environment

**Namespaces:** Staging and production coexist in one cluster, separated by namespace. Simpler operationally. One set of cluster add-ons. Less cost.

The risk: a misconfiguration in one namespace can affect others. Staging pods can talk to production pods by default (no network isolation without NetworkPolicies). A cluster-level incident takes both down.

**Separate clusters:** Production is isolated. Independent upgrade schedules. Network-level separation by default. Better blast radius control.

The cost: every cluster needs its own add-ons, monitoring, ingress, certificates. Operational overhead multiplies.

The common pragmatic answer: **production gets its own cluster; staging and dev share a cluster** (separated by namespace or by a small staging cluster). This limits blast radius for what matters most while keeping operational complexity manageable.

## Environment-specific configuration

Use Kustomize overlays or Helm values files to express environment differences:

```yaml
# overlays/production/kustomization.yaml
patches:
  - path: production-resources.yaml   # higher resource limits
  - path: production-replicas.yaml    # more replicas

images:
  - name: my-app
    newTag: "v1.4.2"                  # pinned release version
```

```yaml
# overlays/staging/kustomization.yaml
patches:
  - path: staging-resources.yaml      # smaller limits to save cost

images:
  - name: my-app
    newTag: "main-abc123"             # latest main branch build
```

The structure makes the difference explicit and reviewable.

## Promotion mechanics with ArgoCD

Each environment gets its own ArgoCD Application pointing at its overlay:

```yaml
# Staging Application
spec:
  source:
    path: overlays/staging

# Production Application
spec:
  source:
    path: overlays/production
```

Staging auto-syncs on every main branch build (CI updates the image tag). Production requires a manual sync — or a promotion PR that updates the production overlay's image tag, reviewed and merged by a human.

The promotion flow:
1. CI builds image `v1.4.2`, updates staging overlay → staging deploys automatically
2. QA runs on staging, passes
3. Engineer opens a PR updating `overlays/production/kustomization.yaml` to `v1.4.2`
4. PR is reviewed, approved, and merged
5. ArgoCD detects the production manifest change → syncs production

Every production deployment is a Git commit with a reviewer and a timestamp. Rollback is reverting the commit.

## Requiring approval before production

In ArgoCD, set the production Application to manual sync:

```yaml
syncPolicy:
  automated: null   # disable automatic sync
```

Deploys to production require someone to click "Sync" in the ArgoCD UI (or run `argocd app sync production`). Combine with ArgoCD RBAC to restrict who can trigger production syncs.

In GitHub Actions, use environment protection rules to require reviewers before a production deployment job runs.

<!-- RESOURCES -->

- [ArgoCD Multi-Cluster Management](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/#clusters) -- type: docs, time: 20m
- [Kubernetes Docs - Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) -- type: docs, time: 10m

<!-- ZH_SUMMARY -->
预发布环境的存在是为了在生产环境之前发现问题。但预发布环境只有在与生产环境高度相似，且两者之间的晋升是有意为之——而非自动、非偶然——的情况下，才能提供价值。

<!-- ZH_DEEP_DIVE -->
## 各环境的用途

**开发环境** — 快速迭代，稳定性要求宽松。开发者需要频繁部署；破坏性变更可以接受。可以是共享集群中的命名空间。

**预发布环境** — 类生产环境。相同的 Kubernetes 版本、相同的资源限制、相同的网络配置。标准是：“这会在生产环境出问题吗？”集成测试、负载测试和人工 QA 在此进行。

**生产环境** — 真实环境。变更需谨慎。部署需要审批。回滚是演练过的，而非临时发挥。

在资源只有生产环境一半的小型廉价集群上运行预发布环境是个错误。你会在生产环境发现预发布环境从未暴露过的资源相关缺陷。

## 每环境一命名空间 vs 每环境一集群

**命名空间：** 预发布和生产共存于一个集群，通过命名空间隔离。运维更简单。一套集群附加组件。成本更低。

风险：一个命名空间的错误配置可能影响其他命名空间。默认情况下预发布 Pod 可以与生产 Pod 通信（没有 NetworkPolicies 就没有网络隔离）。集群级故障会同时拖垮两者。

**独立集群：** 生产环境隔离。独立的升级计划。默认网络级隔离。更好的爆炸半径控制。

代价：每个集群都需要自己的附加组件、监控、Ingress、证书。运维开销成倍增加。

常见的务实答案：**生产环境使用独立集群；预发布和开发共享一个集群**（通过命名空间隔离，或使用一个小型预发布集群）。这样在最关键的部分限制了爆炸半径，同时保持运维复杂度可控。

## 环境特定配置

使用 Kustomize overlay 或 Helm values 文件来表达环境差异：

```yaml
# overlays/production/kustomization.yaml
patches:
  - path: production-resources.yaml   # higher resource limits
  - path: production-replicas.yaml    # more replicas

images:
  - name: my-app
    newTag: "v1.4.2"                  # pinned release version
```

```yaml
# overlays/staging/kustomization.yaml
patches:
  - path: staging-resources.yaml      # smaller limits to save cost

images:
  - name: my-app
    newTag: "main-abc123"             # latest main branch build
```

这种结构使差异显式且可审查。

## 使用 ArgoCD 的晋升机制

每个环境都有自己的 ArgoCD Application，指向其 overlay：

```yaml
# Staging Application
spec:
  source:
    path: overlays/staging

# Production Application
spec:
  source:
    path: overlays/production
```

预发布在每次 main 分支构建时自动同步（CI 更新镜像标签）。生产需要手动同步——或者通过一个晋升 PR 更新生产 overlay 的镜像标签，由人工审查并合并。

晋升流程：
1. CI 构建镜像 `v1.4.2`，更新预发布 overlay → 预发布自动部署
2. QA 在预发布上运行，通过
3. 工程师提交 PR，将 `overlays/production/kustomization.yaml` 更新为 `v1.4.2`
4. PR 被审查、批准并合并
5. ArgoCD 检测到生产清单变更 → 同步生产

每次生产部署都是一个带有审查者和时间戳的 Git 提交。回滚就是还原该提交。

## 生产部署前需要审批

在 ArgoCD 中，将生产 Application 设置为手动同步：

```yaml
syncPolicy:
  automated: null   # disable automatic sync
```

生产部署需要有人在 ArgoCD UI 中点击“Sync”（或运行 `argocd app sync production`）。结合 ArgoCD RBAC 限制谁可以触发生产同步。

在 GitHub Actions 中，使用环境保护规则要求在生产部署任务运行前进行审查。

<!-- ZH_RESOURCES -->
- [ArgoCD 多集群管理](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/#clusters) -- 类型：文档，时长：20 分钟
- [Kubernetes 文档 - 命名空间](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) -- 类型：文档，时长：10 分钟

<!-- ZH_UI -->
1. 将预发和生产分离到不同的命名空间或集群
2. 通过拉取请求将发布从预发晋升到生产
3. 使用 Helm values 或 Kustomize overlays 理解环境特定配置
4. 生产部署前要求手动审批
5. 我的应用跨环境部署——但如何确保它不会耗尽资源或拖垮其他 pod？
6. 在预发环境我不太关心资源使用。但在生产环境我担心一个行为异常的 pod 可能耗尽所有内存并拖垮其他一切。我该如何真正防止这种情况？
7. 一切都在运行。但服务之间如何安全通信，我又如何知道出了什么问题？
8. 我的服务在集群内通过明文 HTTP 通信。我听说从安全角度看这不太好。而且当请求在链路中某处失败时，我无法看到是哪个服务负责。
9. 我应该为每个环境使用单独的命名空间还是单独的集群？
10. 我一直用命名空间来分离预发和生产，但我不确定这是否提供了真正的隔离。到底是什么在阻止一个配置错误的预发 pod 访问生产数据库？
11. 如何阻止一个环境中的服务意外与另一个环境中的服务通信？
12. 预发和生产在同一个集群中。我一直担心预发中配置错误的服务可能意外调用生产 API 或数据库。目前网络层面没有任何东西阻止这种情况发生。
