---
id: secrets
title: Secrets
zone: kubernetes
edges:
  to:
    - id: autoscaling
      question: >-
        Config and secrets are managed. Now — how do I make my workloads scale
        automatically with traffic?
      detail: >-
        My app is running and configured correctly. But right now I have to
        manually change the replica count when traffic spikes. I want it to just
        grow when load increases and shrink when it drops — without me touching
        anything. How does Kubernetes do that automatically?
    - id: resource-requests-and-limits
      question: >-
        Before I set up autoscaling — I've heard Kubernetes needs resource
        requests defined first. What are those?
      detail: >-
        I want autoscaling to work, but I have a feeling I'm missing something.
        My Pods don't have resource requests set — does that matter? How does
        Kubernetes even know what 'high load' means for my app if I haven't told
        it how much CPU or memory each Pod is supposed to use?
difficulty: 1
tags:
  - kubernetes
  - secrets
  - security
  - credentials
  - encryption
  - external-secrets
  - k8s
category: practice
milestones:
  - Create a Secret and inject it as an environment variable into a Pod
  - Understand why base64 encoding is not encryption
  - Enable encryption at rest for Secrets in etcd
  - >-
    Use the External Secrets Operator to sync a secret from AWS Secrets Manager
    or Vault
title_zh: "机密"

---


Kubernetes Secrets hold sensitive data — passwords, API keys, TLS certificates, tokens. They look and work like ConfigMaps but with tighter access controls and optional encryption at rest. The critical caveat: Kubernetes Secrets are base64-encoded by default, which is encoding, not encryption.

<!-- DEEP_DIVE -->

## What Secrets are (and aren't)

A Kubernetes Secret stores sensitive data as key-value pairs. You inject it as environment variables or mount it as files, exactly like a ConfigMap. The difference is in the access model:

- Secrets require explicit RBAC permissions to read (whereas ConfigMaps in the same namespace are broadly readable)
- Kubernetes can audit Secret access separately
- etcd can encrypt Secrets at rest (not enabled by default on most clusters)
- Values are base64-encoded in the API (not plain text like ConfigMap data)

**Base64 is not encryption.** Anyone who can read a Secret can base64-decode it in seconds. The security comes from RBAC and etcd encryption, not from the encoding format.

## Creating a Secret

Imperatively (kubectl handles the base64 encoding for you):

```bash
kubectl create secret generic db-credentials \
  --from-literal=username=postgres \
  --from-literal=password=supersecret
```

Or from YAML (you must base64-encode the values yourself):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: default
type: Opaque
data:
  username: cG9zdGdyZXM=      # base64("postgres")
  password: c3VwZXJzZWNyZXQ=  # base64("supersecret")
```

## Injecting Secrets into Pods

As environment variables — all keys:

```yaml
envFrom:
  - secretRef:
      name: db-credentials
```

Selectively:

```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-credentials
        key: password
```

As mounted files (for TLS certs, kubeconfig files, SSH keys):

```yaml
volumeMounts:
  - name: certs
    mountPath: /etc/ssl/certs
    readOnly: true
volumes:
  - name: certs
    secret:
      secretName: my-tls-cert
```

## Encryption at rest

By default, Secrets are stored unencrypted in etcd. Anyone with direct etcd access can read them. To enable encryption, configure an `EncryptionConfiguration` on the API server to encrypt Secret data using AES-GCM, AES-CBC, or a KMS provider. On managed clusters, EKS and GKE offer this as a configurable option — enable it.

## Don't put Secrets in Git

The obvious problem with Kubernetes Secrets as YAML files: you can't commit them to Git without committing the secrets. Two common solutions:

**External Secrets Operator (ESO)** — you write an `ExternalSecret` resource that references a secret in an external store (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager). ESO fetches the value and creates a regular Kubernetes Secret. Your Git repository only contains the reference, never the value. This is the recommended approach for GitOps workflows.

**Sealed Secrets** — you encrypt Secrets with a public key, commit the encrypted `SealedSecret` to Git, and a controller in the cluster decrypts them using the private key. The encrypted form is safe to commit; only the controller can decrypt it.

<!-- RESOURCES -->

- [Kubernetes Docs - Secrets](https://kubernetes.io/docs/concepts/configuration/secret/) -- type: docs, time: 25m
- [External Secrets Operator](https://external-secrets.io/) -- type: tool, time: 30m
- [Sealed Secrets - Bitnami](https://github.com/bitnami-labs/sealed-secrets) -- type: tool, time: 20m
- [Kubernetes Secret Encryption at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
Kubernetes Secrets 用于保存敏感数据——密码、API 密钥、TLS 证书、令牌。它们的外观和工作方式与 ConfigMap 类似，但具有更严格的访问控制，并可选启用静态加密。关键注意事项：Kubernetes Secrets 默认采用 base64 编码，这是编码，而非加密。

<!-- ZH_DEEP_DIVE -->
## Secret 是什么（以及不是什么）

Kubernetes Secret 以键值对的形式存储敏感数据。你可以像使用 ConfigMap 一样，将其注入为环境变量或挂载为文件。区别在于访问模型：

- Secret 需要显式的 RBAC 权限才能读取（而同一命名空间中的 ConfigMap 通常可被广泛读取）
- Kubernetes 可以单独审计 Secret 的访问
- etcd 可以对 Secret 进行静态加密（大多数集群默认未启用）
- 在 API 中，值以 base64 编码（而非像 ConfigMap 数据那样的明文）

**Base64 不是加密。** 任何能读取 Secret 的人都能在几秒内完成 base64 解码。安全性来自 RBAC 和 etcd 加密，而非编码格式。

## 创建 Secret

命令式创建（kubectl 会替你完成 base64 编码）：

```bash
kubectl create secret generic db-credentials \
  --from-literal=username=postgres \
  --from-literal=password=supersecret
```

或通过 YAML 创建（你需要自行对值进行 base64 编码）：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: default
type: Opaque
data:
  username: cG9zdGdyZXM=      # base64("postgres")
  password: c3VwZXJzZWNyZXQ=  # base64("supersecret")
```

## 将 Secret 注入 Pod

作为环境变量——注入所有键：

```yaml
envFrom:
  - secretRef:
      name: db-credentials
```

选择性注入：

```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-credentials
        key: password
```

作为挂载文件（用于 TLS 证书、kubeconfig 文件、SSH 密钥）：

```yaml
volumeMounts:
  - name: certs
    mountPath: /etc/ssl/certs
    readOnly: true
volumes:
  - name: certs
    secret:
      secretName: my-tls-cert
```

## 静态加密

默认情况下，Secret 以未加密形式存储在 etcd 中。任何能直接访问 etcd 的人都可以读取它们。要启用加密，请在 API server 上配置 `EncryptionConfiguration`，使用 AES-GCM、AES-CBC 或 KMS 提供程序来加密 Secret 数据。在托管集群上，EKS 和 GKE 将此作为可配置选项提供——请启用它。

## 不要把 Secret 放进 Git

将 Kubernetes Secret 作为 YAML 文件使用有一个显而易见的问题：你无法在不提交密钥的情况下将其提交到 Git。两种常见的解决方案：

**External Secrets Operator (ESO)** —— 你编写一个 `ExternalSecret` 资源，引用外部存储（AWS Secrets Manager、HashiCorp Vault、GCP Secret Manager）中的密钥。ESO 获取该值并创建一个常规的 Kubernetes Secret。你的 Git 仓库只包含引用，绝不包含值。这是 GitOps 工作流的推荐做法。

**Sealed Secrets** —— 你用公钥加密 Secret，将加密后的 `SealedSecret` 提交到 Git，集群中的控制器使用私钥对其进行解密。加密形式可以安全提交；只有控制器才能解密它。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Secrets](https://kubernetes.io/docs/concepts/configuration/secret/) -- 类型: 文档, 时间: 25m
- [External Secrets Operator](https://external-secrets.io/) -- 类型: 工具, 时间: 30m
- [Sealed Secrets - Bitnami](https://github.com/bitnami-labs/sealed-secrets) -- 类型: 工具, 时间: 20m
- [Kubernetes Secret 静态加密](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) -- 类型: 文档, 时间: 20m

<!-- ZH_UI -->
1. 创建 Secret 并将其作为环境变量注入 Pod
2. 理解为什么 base64 编码不是加密
3. 为 etcd 中的 Secret 启用静态加密
4. 使用 External Secrets Operator 从 AWS Secrets Manager 或 Vault 同步密钥
5. 配置和密钥已管理好。那么——如何让工作负载随流量自动扩缩容？
6. 我的应用已运行且配置正确。但现在流量激增时我得手动改副本数。我希望负载上升时自动扩容、下降时自动缩容——无需我干预。Kubernetes 如何自动做到这一点？
7. 在设置自动扩缩容之前——我听说 Kubernetes 需要先定义资源请求。那是什么？
8. 我想让自动扩缩容生效，但感觉漏了什么。我的 Pod 没设资源请求——这有影响吗？如果我没告诉 Kubernetes 每个 Pod 该用多少 CPU 或内存，它怎么知道对我的应用来说什么叫“高负载”？
