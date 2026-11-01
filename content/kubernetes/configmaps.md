---
id: configmaps
title: ConfigMaps
zone: kubernetes
edges:
  to:
    - id: secrets
      question: >-
        ConfigMaps work for non-sensitive config. What about passwords, API
        keys, and certificates?
      detail: >-
        I've put my database URL and feature flags in a ConfigMap, but now I
        need to add a database password and an API key. Those feel very
        different — I shouldn't just dump them in the same place as regular
        config. How does Kubernetes handle sensitive values?
difficulty: 1
tags:
  - kubernetes
  - configmap
  - configuration
  - environment-variables
  - k8s
category: practice
milestones:
  - Create a ConfigMap and inject it as environment variables into a Pod
  - Mount a ConfigMap as a config file inside a Pod
  - Update a ConfigMap and understand when the change propagates to running Pods
  - Explain why ConfigMaps are not appropriate for sensitive data
title_zh: "ConfigMap"

---


ConfigMaps store non-sensitive configuration data in Kubernetes — database URLs, feature flags, environment-specific settings. They decouple configuration from your container image, so you can change config without rebuilding, and run the same image in dev and production with different settings.

<!-- DEEP_DIVE -->

## The problem: config baked into images

The naive approach is to hardcode config into the container image. This breaks down immediately in practice:

- Different environments (dev, staging, prod) need different values
- Every config change requires a new image build, push, and deployment
- Config and code go through the same slow release cycle even when only config changed

The Kubernetes answer: externalize config into ConfigMaps and inject them at Pod start time.

## Creating a ConfigMap

From YAML (the preferred, declarative way):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: default
data:
  DATABASE_HOST: "postgres.default.svc.cluster.local"
  DATABASE_PORT: "5432"
  LOG_LEVEL: "info"
  FEATURE_NEW_UI: "true"
```

Or imperatively:

```bash
kubectl create configmap app-config \
  --from-literal=DATABASE_HOST=postgres.default.svc.cluster.local \
  --from-literal=LOG_LEVEL=info
```

Or from a file:

```bash
kubectl create configmap nginx-config --from-file=nginx.conf
```

## Injecting as environment variables

The most common pattern — all keys in the ConfigMap become environment variables in the container:

```yaml
spec:
  containers:
    - name: app
      image: my-app:1.0
      envFrom:
        - configMapRef:
            name: app-config
```

Or selectively, picking specific keys:

```yaml
env:
  - name: DB_HOST
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: DATABASE_HOST
```

## Mounting as files

For config in file format (nginx.conf, application.yaml, etc.), mount the ConfigMap as a volume:

```yaml
spec:
  containers:
    - name: app
      volumeMounts:
        - name: config
          mountPath: /etc/app/config.yaml
          subPath: config.yaml    # mount a single key as a named file
  volumes:
    - name: config
      configMap:
        name: app-config
```

The `subPath` field mounts a single key as a file, rather than creating a directory containing every key as a separate file.

## When changes propagate

- **Environment variables** — do not update in running containers. The Pod must be restarted to pick up changes (update the ConfigMap, then trigger a rolling restart: `kubectl rollout restart deployment/my-app`).
- **Mounted files** — update automatically in running Pods, typically within a minute. The kubelet watches for ConfigMap changes and updates the mounted files. Whether your app notices depends on whether it re-reads the file at runtime or only reads it on startup.

## ConfigMaps are not for secrets

ConfigMaps are stored in etcd in plain text and are readable by anyone with access to the namespace. Don't put passwords, API keys, TLS certificates, or any sensitive data in a ConfigMap — use Secrets for those.

<!-- RESOURCES -->

- [Kubernetes Docs - ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/) -- type: docs, time: 20m
- [Kubernetes Docs - Configure a Pod to Use a ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/) -- type: tutorial, time: 20m

<!-- ZH_SUMMARY -->
ConfigMap 在 Kubernetes 中存储非敏感的配置数据——数据库 URL、功能开关、环境特定设置。它们将配置与容器镜像解耦，因此你无需重新构建即可更改配置，并可在开发和生产环境中使用不同的设置运行同一个镜像。

<!-- ZH_DEEP_DIVE -->
## 问题：配置被固化到镜像中

最朴素的做法是把配置硬编码到容器镜像里。这在实践中会立刻暴露出问题：

- 不同环境（dev、staging、prod）需要不同的配置值
- 每次配置变更都需要重新构建镜像、推送并部署
- 即使只改了配置，配置和代码也要走同一套缓慢的发布流程

Kubernetes 的答案是：把配置外置到 ConfigMap 中，并在 Pod 启动时注入。

## 创建 ConfigMap

通过 YAML（首选的声明式方式）：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: default
data:
  DATABASE_HOST: "postgres.default.svc.cluster.local"
  DATABASE_PORT: "5432"
  LOG_LEVEL: "info"
  FEATURE_NEW_UI: "true"
```

或使用命令式方式：

```bash
kubectl create configmap app-config \
  --from-literal=DATABASE_HOST=postgres.default.svc.cluster.local \
  --from-literal=LOG_LEVEL=info
```

或从文件创建：

```bash
kubectl create configmap nginx-config --from-file=nginx.conf
```

## 以环境变量方式注入

最常见的模式——ConfigMap 中的所有键都会成为容器中的环境变量：

```yaml
spec:
  containers:
    - name: app
      image: my-app:1.0
      envFrom:
        - configMapRef:
            name: app-config
```

或选择性地只取特定键：

```yaml
env:
  - name: DB_HOST
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: DATABASE_HOST
```

## 以文件方式挂载

对于文件格式的配置（nginx.conf、application.yaml 等），将 ConfigMap 挂载为卷：

```yaml
spec:
  containers:
    - name: app
      volumeMounts:
        - name: config
          mountPath: /etc/app/config.yaml
          subPath: config.yaml    # 将单个键挂载为指定名称的文件
  volumes:
    - name: config
      configMap:
        name: app-config
```

`subPath` 字段将单个键挂载为一个文件，而不是创建一个目录、把每个键都作为单独的文件放进去。

## 变更何时生效

- **环境变量**——不会在运行中的容器里更新。必须重启 Pod 才能获取变更（更新 ConfigMap，然后触发滚动重启：`kubectl rollout restart deployment/my-app`）。
- **挂载的文件**——会在运行中的 Pod 中自动更新，通常在约一分钟内完成。kubelet 会监听 ConfigMap 的变更并更新挂载的文件。你的应用能否感知到，取决于它是在运行时重新读取文件，还是只在启动时读取一次。

## ConfigMap 不用于存放密钥

ConfigMap 以明文形式存储在 etcd 中，任何对该命名空间有访问权限的人都能读取。不要把密码、API 密钥、TLS 证书或任何敏感数据放进 ConfigMap——这些应使用 Secret。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - ConfigMap](https://kubernetes.io/docs/concepts/configuration/configmap/) -- 类型：文档，时长：20m
- [Kubernetes 文档 - 配置 Pod 使用 ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/) -- 类型：教程，时长：20m

<!-- ZH_UI -->
1. 创建 ConfigMap 并将其作为环境变量注入 Pod
2. 将 ConfigMap 作为配置文件挂载到 Pod 内
3. 更新 ConfigMap 并理解变更何时传播到运行中的 Pod
4. 解释为什么 ConfigMap 不适合存放敏感数据
5. ConfigMap 适用于非敏感配置。那密码、API 密钥和证书呢？
6. 我已将数据库 URL 和功能开关放入 ConfigMap，但现在需要添加数据库密码和 API 密钥。这两类数据感觉完全不同——我不应该把它们和普通配置放在同一个地方。Kubernetes 如何处理敏感值？
