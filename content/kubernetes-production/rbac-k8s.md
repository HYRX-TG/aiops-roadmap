---
id: rbac-k8s
title: RBAC and Access Control in Kubernetes
zone: kubernetes-production
edges:
  to:
    - id: network-policies
      question: >-
        I've locked down who can deploy to the cluster. But I just realized any
        pod can still reach any other pod freely.
      detail: >-
        My payment service could make HTTP calls to my internal admin API. A
        compromised pod in one namespace could try to hit the database in
        another. I've controlled what people can do via kubectl, but once a pod
        is running it seems like it can talk to anything. That can't be right.
difficulty: 3
tags:
  - kubernetes
  - rbac
  - roles
  - clusterroles
  - service-accounts
  - authorization
  - k8s
  - production
  - security
category: concept
milestones:
  - >-
    Understand the RBAC building blocks: Role, ClusterRole, RoleBinding,
    ClusterRoleBinding — and when to use each
  - >-
    Know the difference between namespace-scoped Roles and cluster-wide
    ClusterRoles, and why giving everyone a ClusterRole is the common mistake
  - >-
    Set up a ServiceAccount for your CI/CD pipeline with only the permissions
    it needs — not cluster-admin
  - >-
    Know the principle of least privilege in practice: verbs (get, list, watch,
    create, delete) mapped to specific resources per namespace
  - >-
    Use kubectl auth can-i to audit what a user or service account can
    actually do
title_zh: "Kubernetes 中的 RBAC 与访问控制"

---


Kubernetes RBAC controls what actions subjects (users, service accounts, CI systems) can take through the Kubernetes API. By default, new service accounts have no permissions. The common mistake is solving that by assigning `cluster-admin` — which grants god-mode to anything that holds the token.

<!-- DEEP_DIVE -->

## The building blocks

**Role** — a set of permissions scoped to a single namespace. Can only grant access to namespace-scoped resources (pods, deployments, secrets, services).

**ClusterRole** — a set of permissions that applies cluster-wide, or can be used to grant access to cluster-scoped resources (nodes, StorageClasses, PersistentVolumes, namespaces themselves).

**RoleBinding** — binds a Role (or ClusterRole) to subjects within a specific namespace.

**ClusterRoleBinding** — binds a ClusterRole to subjects cluster-wide.

The key distinction: a ClusterRoleBinding grants access everywhere. A RoleBinding with a ClusterRole as the role reference grants that role's permissions within the binding's namespace only.

## Subjects: who gets bound

RBAC subjects are:
- **User** — Kubernetes doesn't manage users. It trusts the authentication layer (certificates, OIDC tokens from your identity provider). A user "alice" means whatever auth system you've configured says the token belongs to alice.
- **Group** — similarly delegated to the auth layer. OIDC providers can include group claims.
- **ServiceAccount** — a namespaced Kubernetes object. Pods run as service accounts and can be bound to roles. This is how pods get API access.

## The CI/CD service account

Your CI system needs to deploy to the cluster. The wrong solution: give it `cluster-admin`.

The right solution: a service account with exactly the permissions it needs:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer
  namespace: production
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "update", "patch"]
  - apiGroups: [""]
    resources: ["services", "configmaps"]
    verbs: ["get", "list", "update", "patch", "create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ci-deployer
  namespace: production
subjects:
  - kind: ServiceAccount
    name: ci-runner
    namespace: ci
roleRef:
  kind: Role
  name: deployer
  apiGroup: rbac.authorization.k8s.io
```

This service account can update deployments and services in `production` — and nothing else. If the CI system is compromised, the attacker can deploy a bad image, but can't read secrets from other namespaces, delete arbitrary resources, or access cluster-level configuration.

## The principle of least privilege in practice

The verbs available are: `get`, `list`, `watch`, `create`, `update`, `patch`, `delete`, `deletecollection`. Grant the minimum set required for the task:

- Operators that read resource state: `get`, `list`, `watch`
- Deployment systems: `get`, `list`, `update`, `patch`, `create` on specific resource types
- Never `*` on resources or verbs unless there's no alternative

Namespace isolation: use Roles (not ClusterRoles) for permissions that should be namespace-scoped. A developer should be able to `kubectl logs` in their own namespace, not across the cluster.

## Auditing permissions

```bash
# Can alice delete pods in the production namespace?
kubectl auth can-i delete pods --namespace production --as alice

# What can the ci-runner service account do in production?
kubectl auth can-i --list --namespace production \
  --as system:serviceaccount:ci:ci-runner
```

Use these commands to verify permissions are what you expect before committing to a configuration. `--list` with `can-i` shows all permissions available to a subject.

## The common mistakes

**cluster-admin for developers** — given "temporarily" to unblock someone, never revoked. Audit your ClusterRoleBindings regularly.

**Shared service accounts** — multiple services using the same service account. If one is compromised, you can't revoke just that one.

**No RBAC for workloads** — pods defaulting to the `default` service account, which has no permissions by default but can be accidentally over-permissioned. Create dedicated service accounts for each workload.

<!-- RESOURCES -->

- [Kubernetes Docs - RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) -- type: docs, time: 30m
- [Kubernetes Docs - Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#using-rbac-authorization) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
Kubernetes RBAC 控制主体（用户、服务账号、CI 系统）可以通过 Kubernetes API 执行哪些操作。默认情况下，新建的服务账号没有任何权限。常见的错误是通过分配 `cluster-admin` 来解决这个问题——这会把上帝模式授予任何持有该令牌的对象。

<!-- ZH_DEEP_DIVE -->
## 构建块

**Role** — 一组限定在单个命名空间内的权限。只能授予对命名空间级资源（pods、deployments、secrets、services）的访问权限。

**ClusterRole** — 一组应用于集群范围的权限，或可用于授予对集群级资源（nodes、StorageClasses、PersistentVolumes、命名空间本身）的访问权限。

**RoleBinding** — 将 Role（或 ClusterRole）绑定到特定命名空间内的主体。

**ClusterRoleBinding** — 将 ClusterRole 绑定到集群范围内的主体。

关键区别：ClusterRoleBinding 授予所有位置的访问权限。以 ClusterRole 作为角色引用的 RoleBinding 仅在该绑定所在的命名空间内授予该角色的权限。

## 主体：谁被绑定

RBAC 主体包括：
- **User** — Kubernetes 不管理用户。它信任认证层（证书、来自身份提供商的 OIDC 令牌）。用户 "alice" 意味着你所配置的认证系统表明该令牌属于 alice。
- **Group** — 同样委托给认证层。OIDC 提供商可以包含组声明。
- **ServiceAccount** — 一个命名空间级的 Kubernetes 对象。Pod 以服务账户身份运行，并且可以绑定到角色。这就是 Pod 获得 API 访问权限的方式。

## CI/CD 服务账户

你的 CI 系统需要部署到集群。错误的解决方案：给它 `cluster-admin`。

正确的解决方案：一个仅具有其所需权限的服务账户：

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer
  namespace: production
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "update", "patch"]
  - apiGroups: [""]
    resources: ["services", "configmaps"]
    verbs: ["get", "list", "update", "patch", "create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ci-deployer
  namespace: production
subjects:
  - kind: ServiceAccount
    name: ci-runner
    namespace: ci
roleRef:
  kind: Role
  name: deployer
  apiGroup: rbac.authorization.k8s.io
```

该服务账户可以更新 `production` 中的 deployments 和 services——仅此而已。如果 CI 系统被攻破，攻击者可以部署恶意镜像，但无法读取其他命名空间中的 secrets、删除任意资源或访问集群级配置。

## 最小权限原则的实践

可用的动词包括：`get`、`list`、`watch`、`create`、`update`、`patch`、`delete`、`deletecollection`。授予任务所需的最小集合：

- 读取资源状态的 Operator：`get`、`list`、`watch`
- 部署系统：对特定资源类型的 `get`、`list`、`update`、`patch`、`create`
- 除非别无选择，否则绝不要对资源或动词使用 `*`

命名空间隔离：对于应限定在命名空间范围内的权限，使用 Role（而非 ClusterRole）。开发者应能在自己的命名空间中执行 `kubectl logs`，而不是在整个集群范围内。

## 审计权限

```bash
# Can alice delete pods in the production namespace?
kubectl auth can-i delete pods --namespace production --as alice

# What can the ci-runner service account do in production?
kubectl auth can-i --list --namespace production \
  --as system:serviceaccount:ci:ci-runner
```

在提交配置之前，使用这些命令验证权限是否符合预期。`can-i` 配合 `--list` 会显示某个主体可用的所有权限。

## 常见错误

**为开发者授予 cluster-admin** — 以"临时"为由授予某人以解除阻塞，却从未撤销。定期审计你的 ClusterRoleBindings。

**共享服务账户** — 多个服务使用同一个服务账户。如果其中一个被攻破，你无法只撤销那一个。

**工作负载没有 RBAC** — Pod 默认使用 `default` 服务账户，该账户默认没有权限，但可能被意外授予过多权限。为每个工作负载创建专用的服务账户。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - RBAC 授权](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) -- type: docs, time: 30m
- [Kubernetes 文档 - 使用 RBAC 授权](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#using-rbac-authorization) -- type: docs, time: 20m

<!-- ZH_UI -->
1. 理解 RBAC 的基本构建块：Role、ClusterRole、RoleBinding、ClusterRoleBinding——以及各自适用的场景
2. 了解命名空间级 Role 与集群级 ClusterRole 的区别，以及为什么给所有人分配 ClusterRole 是常见错误
3. 为 CI/CD 流水线配置一个仅具备所需权限的 ServiceAccount——而不是 cluster-admin
4. 在实践中理解最小权限原则：将动词（get、list、watch、create、delete）按命名空间映射到特定资源
5. 使用 kubectl auth can-i 审计用户或服务账号实际能执行的操作
6. 我已经限制了谁可以部署到集群。但我刚意识到任何 Pod 仍然可以自由访问其他任何 Pod。
7. 我的支付服务可以向内部管理 API 发起 HTTP 调用。一个命名空间中被攻陷的 Pod 可以尝试访问另一个命名空间中的数据库。我已经通过 kubectl 控制了人们能做什么，但 Pod 一旦运行起来似乎可以和任何东西通信。这不对劲。
