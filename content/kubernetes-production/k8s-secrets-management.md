---
id: k8s-secrets-management
title: Secrets Management in Kubernetes
zone: kubernetes-production
edges:
  to:
    - id: rbac-k8s
      question: >-
        I've got secrets stored safely. But how do I control which services and
        people are actually allowed to read them?
      detail: >-
        Any pod that knows the secret name can read it right now. I need a way
        to say "only the payment service gets the payment API key" — not just
        control what's in the secret, but who can access it.
difficulty: 3
tags:
  - kubernetes
  - secrets
  - sealed-secrets
  - external-secrets
  - vault
  - etcd
  - k8s
  - production
category: concept
milestones:
  - Understand why native K8s Secrets are base64 — not encrypted — by default
  - >-
    Know the etcd problem: secrets are stored unencrypted unless you configure
    encryption at rest
  - >-
    Know the spectrum: Sealed Secrets → External Secrets Operator → HashiCorp
    Vault
  - >-
    Understand when to reach for each: ESO + cloud secret store is the most
    common production pattern
title_zh: "Kubernetes 中的 Secrets 管理"

---


Kubernetes Secrets are not secret by default. They're base64-encoded — which is encoding, not encryption. Anyone with read access to the Secret object sees the value. And if you commit them to Git, they're effectively plaintext in your repository history. Production requires a real secrets strategy.

<!-- DEEP_DIVE -->

## The native Secret problem

```bash
kubectl get secret my-db-password -o jsonpath='{.data.password}' | base64 -d
```

That's all it takes to read a Kubernetes Secret if you have `get` permission on secrets in that namespace. Base64 is trivially reversible.

By default, etcd also stores secrets unencrypted. If someone gains access to etcd — or an etcd backup — they have all your secrets. This is configurable: Kubernetes supports encryption at rest for etcd, which managed clusters like GKE enable by default, while self-managed clusters require explicit configuration.

## Option 1: Sealed Secrets

Sealed Secrets (by Bitnami) lets you commit encrypted secrets to Git. A controller in the cluster holds a private key. You encrypt secrets with the corresponding public key using the `kubeseal` CLI. The encrypted `SealedSecret` is safe to commit — only the cluster's controller can decrypt it.

```bash
kubectl create secret generic db-password \
  --from-literal=password=supersecret \
  --dry-run=client -o yaml | \
  kubeseal --format yaml > sealed-db-password.yaml
```

Commit `sealed-db-password.yaml`. The controller decrypts it and creates the actual Kubernetes Secret. If someone gets your Git repo, they see ciphertext, not the password.

Limitation: if you lose the cluster's private key, you lose the ability to decrypt. Key rotation is manual and requires re-sealing every secret. Good for simple setups; gets unwieldy at scale.

## Option 2: External Secrets Operator (ESO)

ESO syncs secrets from external secret stores (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, HashiCorp Vault) into Kubernetes Secrets automatically.

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-password
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: ClusterSecretStore
  target:
    name: db-password       # name of the Kubernetes Secret to create
  data:
    - secretKey: password
      remoteRef:
        key: production/db-password   # key in AWS Secrets Manager
```

ESO creates and updates the Kubernetes Secret from the external store. Your manifests in Git reference only the ExternalSecret definition — no secret values in Git at all. The actual values live in the cloud secret store.

This is the most common production pattern for cloud-hosted clusters. AWS Secrets Manager, GCP Secret Manager, and Azure Key Vault are all first-class citizens.

## Option 3: HashiCorp Vault

Vault is a full-featured secrets management platform: dynamic secrets, PKI, database credential rotation, audit logging. It can generate short-lived database credentials that expire automatically rather than long-lived static passwords.

The power: a compromised Kubernetes Secret is just a credential that expires soon. Vault's dynamic secrets significantly reduce the blast radius of credential exposure.

The cost: Vault is a complex system to operate. High availability Vault requires distributed consensus (Raft or Consul). You're now running infrastructure to manage your infrastructure.

Vault makes sense when you have: complex credential rotation requirements, strict audit requirements, or multiple platforms (Kubernetes and non-Kubernetes systems) that need centralized secrets.

## The rule: never commit plaintext secrets to Git

Not in comments. Not in values files. Not "just temporarily." Git history is forever, and secret-scanning tools will find them. If you've ever committed a secret, rotate it immediately — you cannot reliably expunge it from Git history everywhere it's been cloned.

Use `.gitignore` to prevent accidental commits. Use pre-commit hooks or tools like `git-secrets` to block them at the commit stage.

## The most common production choice

**ESO + your cloud provider's secret store** is where most teams end up. It's operationally simple (ESO is a single Helm chart), integrates with IAM for access control, and keeps values out of Git entirely. Start here.

<!-- RESOURCES -->

- [Kubernetes Docs - Secrets](https://kubernetes.io/docs/concepts/configuration/secret/) -- type: docs, time: 15m
- [External Secrets Operator](https://external-secrets.io/latest/) -- type: docs, time: 25m
- [Sealed Secrets](https://sealed-secrets.netlify.app/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
Kubernetes Secrets 默认并不保密。它们只是经过 base64 编码——这是编码，不是加密。任何对 Secret 对象有读权限的人都能看到其值。而如果你把它们提交到 Git，它们实际上就以明文形式存在于你的仓库历史中。生产环境需要一套真正的密钥管理策略。

<!-- ZH_DEEP_DIVE -->
## 原生 Secret 的问题

```bash
kubectl get secret my-db-password -o jsonpath='{.data.password}' | base64 -d
```

只要你在该命名空间拥有 secrets 的 `get` 权限，读取 Kubernetes Secret 就只需要这一条命令。Base64 编码可以轻易逆转。

默认情况下，etcd 也以未加密的形式存储 Secret。如果有人获取了 etcd 的访问权限——或者拿到了一份 etcd 备份——他们就掌握了你所有的 Secret。这一点是可配置的：Kubernetes 支持对 etcd 进行静态加密，GKE 等托管集群默认启用该功能，而自管理集群则需要显式配置。

## 方案 1：Sealed Secrets

Sealed Secrets（由 Bitnami 提供）让你可以把加密后的 Secret 提交到 Git。集群中的一个控制器持有私钥。你使用 `kubeseal` CLI 通过对应的公钥加密 Secret。加密后的 `SealedSecret` 可以安全地提交——只有集群中的控制器才能解密它。

```bash
kubectl create secret generic db-password \
  --from-literal=password=supersecret \
  --dry-run=client -o yaml | \
  kubeseal --format yaml > sealed-db-password.yaml
```

提交 `sealed-db-password.yaml`。控制器会解密它并创建实际的 Kubernetes Secret。如果有人拿到了你的 Git 仓库，他们看到的只是密文，而不是密码。

局限：如果你丢失了集群的私钥，你就失去了解密能力。密钥轮换是手动的，并且需要重新封装每一个 Secret。适合简单的场景；在规模化时会变得难以管理。

## 方案 2：External Secrets Operator（ESO）

ESO 会自动将外部 Secret 存储（AWS Secrets Manager、GCP Secret Manager、Azure Key Vault、HashiCorp Vault）中的 Secret 同步到 Kubernetes Secret 中。

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-password
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: ClusterSecretStore
  target:
    name: db-password       # name of the Kubernetes Secret to create
  data:
    - secretKey: password
      remoteRef:
        key: production/db-password   # key in AWS Secrets Manager
```

ESO 会根据外部存储创建并更新 Kubernetes Secret。你在 Git 中的清单只引用 ExternalSecret 定义——Git 中完全没有 Secret 值。实际的值存放在云 Secret 存储中。

这是云托管集群最常见的生产实践模式。AWS Secrets Manager、GCP Secret Manager 和 Azure Key Vault 都是一等公民。

## 方案 3：HashiCorp Vault

Vault 是一个功能完备的 Secret 管理平台：动态 Secret、PKI、数据库凭据轮换、审计日志。它可以生成自动过期的短期数据库凭据，而不是长期有效的静态密码。

优势在于：即使 Kubernetes Secret 被泄露，它也只是一个很快会过期的凭据。Vault 的动态 Secret 显著缩小了凭据暴露的影响范围。

代价在于：Vault 是一个运维复杂的系统。高可用的 Vault 需要分布式共识（Raft 或 Consul）。你现在要运行一套基础设施来管理你的基础设施。

Vault 适用于以下情况：你有复杂的凭据轮换需求、严格的审计要求，或者有多个平台（Kubernetes 和非 Kubernetes 系统）需要集中式 Secret 管理。

## 规则：永远不要把明文 Secret 提交到 Git

不要写在注释里。不要写在 values 文件里。不要“只是临时”提交。Git 历史是永久的，Secret 扫描工具会找到它们。如果你曾经提交过 Secret，请立即轮换它——你无法可靠地将它从所有被克隆过的 Git 历史中彻底清除。

使用 `.gitignore` 防止意外提交。使用 pre-commit 钩子或 `git-secrets` 之类的工具在提交阶段拦截它们。

## 最常见的生产选择

**ESO + 你的云提供商的 Secret 存储**是大多数团队最终采用的方案。它在运维上很简单（ESO 只是一个 Helm chart），与 IAM 集成实现访问控制，并且完全将值排除在 Git 之外。从这里开始。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Secrets](https://kubernetes.io/docs/concepts/configuration/secret/) -- 类型: 文档, 时间: 15m
- [External Secrets Operator](https://external-secrets.io/latest/) -- 类型: 文档, 时间: 25m
- [Sealed Secrets](https://sealed-secrets.netlify.app/) -- 类型: 文档, 时间: 20m

<!-- ZH_UI -->
1. 理解为什么原生 K8s Secrets 默认只是 base64 编码——而非加密
2. 了解 etcd 的问题：除非配置静态加密，否则 secrets 以未加密形式存储
3. 了解演进路线：Sealed Secrets → External Secrets Operator → HashiCorp Vault
4. 理解何时选用哪种方案：ESO + 云密钥存储是最常见的生产模式
5. 我已经安全地存储了 secrets。但如何控制哪些服务和人员真正有权读取它们？
6. 现在任何知道 secret 名称的 pod 都能读取它。我需要一种方式来规定“只有支付服务才能获取支付 API 密钥”——不仅是控制 secret 里存什么，还要控制谁能访问它。
