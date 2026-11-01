---
id: cluster-upgrades
title: Upgrading Kubernetes in Production
zone: kubernetes-production
edges:
  to: []
difficulty: 3
tags:
  - kubernetes
  - upgrades
  - version
  - nodes
  - control-plane
  - drain
  - k8s
  - production
  - operations
category: practice
milestones:
  - >-
    Understand the Kubernetes release cadence: minor versions every ~4 months,
    each supported for ~14 months — falling behind is easy
  - >-
    Know the upgrade order: control plane first, then node groups — and why
    you cannot skip minor versions
  - >-
    Understand how managed clusters (EKS, GKE, AKS) handle control plane
    upgrades vs how you handle node group upgrades
  - >-
    Know the node upgrade strategies: rolling drain-and-replace vs blue-green
    node groups, and what PDBs do during the drain
  - >-
    Test upgrades in staging first — API deprecations between versions break
    things silently (check with kubectl deprecations or pluto)
title_zh: "在生产环境中升级 Kubernetes"

---


Kubernetes releases a new minor version roughly every four months and supports each version for about fourteen months. Fall two versions behind and you're running EOL software with no security patches. Fall three behind and upgrading requires multiple sequential hops. Kubernetes upgrades are not optional — they're a recurring operational responsibility.

<!-- DEEP_DIVE -->

## The release cadence

Kubernetes follows a regular schedule: three minor versions per year (e.g., 1.28, 1.29, 1.30). Each version receives patch releases throughout its support window. Once a version reaches end of life, no more patches — including security fixes.

Managed clusters (EKS, GKE, AKS) sometimes extend support windows beyond the upstream schedule, but eventually force you to upgrade.

The practical rule: stay within two minor versions of the latest release. This gives you time to plan and test upgrades without falling into EOL territory.

## You cannot skip minor versions

Kubernetes guarantees compatibility between adjacent minor versions: the API server at version N supports clients at N-1 and N+1. The upgrade path is sequential: 1.27 → 1.28 → 1.29. Jumping from 1.27 to 1.29 directly is unsupported and will cause failures.

This means if you're two versions behind, you're doing two upgrades. Three behind, three upgrades. The longer you wait, the more work an upgrade becomes.

## The upgrade order: control plane first, then nodes

The control plane (API server, scheduler, controller manager) must be upgraded first. A newer API server is backward-compatible with older kubelet versions for one minor version. You cannot have nodes running newer Kubernetes than the control plane.

For managed clusters, the process is:

1. **Upgrade the control plane** — in EKS, this is done through the console or CLI. In GKE, you select the target version in the node pool configuration. In AKS, `az aks upgrade`.

2. **Upgrade node groups** — after the control plane is upgraded, update each node group to the new version. This triggers a rolling replacement: new nodes come up with the new version, workloads migrate over, old nodes are drained and terminated.

On EKS, upgrading nodes means either launching a new managed node group with the updated AMI (blue-green approach) or using in-place rolling update on the existing node group.

## Node upgrade strategies

**Rolling drain and replace** — nodes are drained one at a time (or in small batches), workloads migrate to remaining nodes, the drained node is replaced with a new one at the new version. Requires enough spare capacity to accommodate the migrating workloads during the drain.

**Blue-green node groups** — create a new node group with the updated version. Wait for it to be healthy. Migrate workloads using taints (taint the old group `NoSchedule`, new workloads land on new group) or by draining old nodes. Delete the old group when empty. Zero-downtime, but requires paying for two full node groups temporarily.

For critical production clusters, blue-green is safer. For most teams, rolling drain works fine with proper PDBs.

## What breaks during upgrades: API deprecations

Kubernetes removes deprecated API versions between minor versions. If your manifests use an API that was removed, they'll fail to apply after the upgrade. This is the most common surprise in Kubernetes upgrades.

Check before upgrading:

```bash
# Install pluto (a tool for detecting deprecated Kubernetes API versions)
# Then scan your manifests
pluto detect-files -d k8s/

# Or use kubectl's built-in deprecation check
kubectl get --raw /apis | grep "apiVersion"
```

Common historical examples: `apps/v1beta1` Deployments (removed in 1.16), `networking.k8s.io/v1beta1` Ingress (removed in 1.22), `autoscaling/v2beta1` HPA (removed in 1.26).

Always check the release notes and deprecation announcements for your target version before upgrading.

## Testing: staging first, always

Upgrade your staging cluster one to two weeks before upgrading production. Run your full suite of integration tests against the upgraded staging cluster. Fix any API deprecation issues or behavior changes before they become production incidents.

If you don't have a staging cluster running the same Kubernetes version as production, you can't safely test upgrades. This is one of the arguments for keeping staging reasonably close to production configuration.

## The managed cluster upgrade workflow (EKS example)

```bash
# Upgrade EKS control plane to 1.29
aws eks update-cluster-version \
  --name my-cluster \
  --kubernetes-version 1.29

# Wait for control plane upgrade to complete
aws eks wait cluster-active --name my-cluster

# Upgrade managed node group
aws eks update-nodegroup-version \
  --cluster-name my-cluster \
  --nodegroup-name general \
  --kubernetes-version 1.29

# Watch node group update status
aws eks describe-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name general \
  --query "nodegroup.status"
```

The node group update triggers rolling replacement. With proper PDBs set, workloads migrate safely during the drain.

<!-- RESOURCES -->

- [Kubernetes Release Notes](https://kubernetes.io/releases/) -- type: docs, time: 15m
- [Kubernetes Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/) -- type: docs, time: 10m
- [Pluto - Kubernetes API Deprecation Detector](https://pluto.docs.fairwinds.com/) -- type: tool, time: 10m
- [AWS EKS Cluster Upgrade](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
Kubernetes 大约每四个月发布一个新的次要版本，每个版本的支持周期约为十四个月。落后两个版本，你运行的便是已停止支持（EOL）的软件，无法获得安全补丁。落后三个版本，升级就需要经过多次连续的版本跳跃。Kubernetes 升级并非可选项——它是一项反复出现的运维职责。

<!-- ZH_DEEP_DIVE -->
## 发布节奏

Kubernetes 遵循固定的发布节奏：每年三个次版本（例如 1.28、1.29、1.30）。每个版本在其支持窗口内会持续收到补丁发布。一旦某个版本到达生命周期终点，就不再有任何补丁——包括安全修复。

托管集群（EKS、GKE、AKS）有时会将支持窗口延长至上游计划之外，但最终仍会强制你升级。

实用规则：与最新版本保持不超过两个次版本的差距。这样你就有时间规划和测试升级，而不会落入 EOL 范围。

## 不能跳过次版本

Kubernetes 保证相邻次版本之间的兼容性：版本 N 的 API server 支持 N-1 和 N+1 的客户端。升级路径是顺序的：1.27 → 1.28 → 1.29。从 1.27 直接跳到 1.29 是不受支持的，会导致失败。

这意味着如果你落后两个版本，就要做两次升级。落后三个版本，就要做三次升级。等待越久，升级的工作量就越大。

## 升级顺序：先控制平面，后节点

控制平面（API server、scheduler、controller manager）必须先升级。较新的 API server 在一个次版本范围内向后兼容较旧的 kubelet 版本。不能让节点运行的 Kubernetes 版本比控制平面更新。

对于托管集群，流程如下：

1. **升级控制平面** —— 在 EKS 中，通过控制台或 CLI 完成。在 GKE 中，在节点池配置中选择目标版本。在 AKS 中，使用 `az aks upgrade`。

2. **升级节点组** —— 控制平面升级完成后，将每个节点组更新到新版本。这会触发滚动替换：新节点以新版本启动，工作负载迁移过去，旧节点被排空并终止。

在 EKS 上，升级节点意味着要么使用更新后的 AMI 启动新的托管节点组（蓝绿方式），要么在现有节点组上使用原地滚动更新。

## 节点升级策略

**滚动排空与替换** —— 节点逐个（或小批量）排空，工作负载迁移到剩余节点，被排空的节点替换为新版本的新节点。需要有足够的空闲容量来容纳排空期间迁移的工作负载。

**蓝绿节点组** —— 创建一个使用更新版本的新节点组。等待其健康。使用污点迁移工作负载（给旧组打上 `NoSchedule` 污点，新工作负载会落到新组上），或通过排空旧节点来迁移。旧组为空后删除。零停机，但需要临时为两个完整节点组付费。

对于关键生产集群，蓝绿更安全。对于大多数团队，配合适当的 PDB，滚动排空即可正常工作。

## 升级期间会出什么问题：API 弃用

Kubernetes 会在次版本之间移除已弃用的 API 版本。如果你的清单使用了已被移除的 API，升级后将无法应用。这是 Kubernetes 升级中最常见的意外。

升级前检查：

```bash
# Install pluto (a tool for detecting deprecated Kubernetes API versions)
# Then scan your manifests
pluto detect-files -d k8s/

# Or use kubectl's built-in deprecation check
kubectl get --raw /apis | grep "apiVersion"
```

常见的历史示例：`apps/v1beta1` Deployment（在 1.16 中移除）、`networking.k8s.io/v1beta1` Ingress（在 1.22 中移除）、`autoscaling/v2beta1` HPA（在 1.26 中移除）。

升级前务必查看目标版本的发布说明和弃用公告。

## 测试：始终先上预发环境

在生产升级前一到两周升级预发集群。针对升级后的预发集群运行完整的集成测试套件。在生产事故之前修复任何 API 弃用问题或行为变更。

如果你没有运行与生产相同 Kubernetes 版本的预发集群，就无法安全地测试升级。这是保持预发环境配置与生产合理接近的论据之一。

## 托管集群升级工作流（EKS 示例）

```bash
# Upgrade EKS control plane to 1.29
aws eks update-cluster-version \
  --name my-cluster \
  --kubernetes-version 1.29

# Wait for control plane upgrade to complete
aws eks wait cluster-active --name my-cluster

# Upgrade managed node group
aws eks update-nodegroup-version \
  --cluster-name my-cluster \
  --nodegroup-name general \
  --kubernetes-version 1.29

# Watch node group update status
aws eks describe-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name general \
  --query "nodegroup.status"
```

节点组更新会触发滚动替换。设置好适当的 PDB 后，工作负载会在排空期间安全迁移。

<!-- ZH_RESOURCES -->
- [Kubernetes 发布说明](https://kubernetes.io/releases/) -- 类型: 文档, 时间: 15m
- [Kubernetes 版本偏差策略](https://kubernetes.io/releases/version-skew-policy/) -- 类型: 文档, 时间: 10m
- [Pluto - Kubernetes API 弃用检测工具](https://pluto.docs.fairwinds.com/) -- 类型: 工具, 时间: 10m
- [AWS EKS 集群升级](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html) -- 类型: 文档, 时间: 20m

<!-- ZH_UI -->
1. 了解 Kubernetes 发布节奏：约每 4 个月发布一个次版本，每个版本支持约 14 个月——很容易落后
2. 了解升级顺序：先控制平面，再节点组——以及为什么不能跳过次版本
3. 理解托管集群（EKS、GKE、AKS）如何处理控制平面升级，以及你如何处理节点组升级
4. 了解节点升级策略：滚动驱逐替换 vs 蓝绿节点组，以及 PDB 在驱逐期间的作用
5. 先在预发环境测试升级——版本间的 API 弃用会静默破坏功能（用 kubectl deprecations 或 pluto 检查）
