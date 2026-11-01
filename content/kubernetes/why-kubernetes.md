---
id: why-kubernetes
title: Why Kubernetes?
zone: kubernetes
edges:
  to:
    - id: pods
      question: Kubernetes makes sense. How do I actually run a container on it?
      detail: >-
        Okay, I want to run my container on this cluster. I know Docker, I know
        docker run — but how do I do the equivalent in Kubernetes? kubectl run?
        A YAML file? And what is this 'Pod' thing I keep seeing in the docs — is
        that just a fancy word for a container?
    - id: namespaces
      question: >-
        Before I run anything — how does Kubernetes keep different teams, apps,
        and environments from interfering with each other?
      detail: >-
        If staging and production both run on the same cluster, and teammates
        are deploying their stuff too — what stops everything from getting
        tangled together? I need some kind of separation before this becomes a
        mess.
difficulty: 1
tags:
  - kubernetes
  - orchestration
  - containers
  - docker
  - k8s
  - devops
category: concept
milestones:
  - Explain what problems Kubernetes solves that Docker Compose alone doesn't
  - Understand the control plane vs worker node distinction
  - Know what kubectl is and how to connect it to a cluster
  - Run a local cluster with kind or minikube
title_zh: "为什么选择 Kubernetes？"

---


Running containers in production means answering hard questions: which server does this container go on? What happens when it crashes? How do you ship a new version without dropping traffic? Kubernetes is the system that answers all of them — and has become the de facto standard for running containers at scale.

<!-- DEEP_DIVE -->

## The problem Kubernetes solves

Docker Compose runs containers on one machine. That works fine for a single server, but production systems have harder problems. You need containers to survive machine failures. You need to run more of them during traffic spikes and fewer when it's quiet. You need to ship new versions without downtime. You need to restart them when they crash. Someone — or something — has to coordinate all of that.

That coordinator is called an **orchestrator**. Kubernetes is the dominant one. It started inside Google (where a similar internal system called Borg had been running for years), was open-sourced in 2014, and became the standard quickly enough that cloud providers essentially had to offer it as a managed service. Today, "container orchestration" and "Kubernetes" are nearly synonymous.

## What Kubernetes actually does

Kubernetes runs your containers on a cluster of machines and continuously works to keep the cluster matching the state you declared. You don't say "run this container on server 3." You say "I want 5 copies of this container running, each with at least 500MB of RAM." Kubernetes picks the servers, starts the containers, and if one crashes, automatically replaces it. If a server dies, the workloads from that server are rescheduled onto healthy ones.

This model — declare the desired state, let the system reconcile reality to match it — is what makes Kubernetes powerful. And it's the source of most of its complexity.

## The control plane and worker nodes

A Kubernetes cluster is split into two parts:

- **Control plane** — the brain. Runs the API server, scheduler, controller manager, and etcd (the cluster's key-value store). The control plane makes decisions: where to schedule a Pod, when to replace a failed one, how to roll out an update.
- **Worker nodes** — the muscle. These are the machines that actually run your containers. Each node runs `kubelet` (communicates with the control plane), `kube-proxy` (handles networking), and a container runtime (usually containerd).

When you use a managed Kubernetes service like EKS, GKE, or AKS, the cloud provider runs the control plane for you. You manage the worker nodes — or let the provider manage those too with managed node groups.

## kubectl — the control plane's interface

Everything you do with Kubernetes goes through `kubectl`, the command-line tool that talks to the Kubernetes API server. `kubectl apply -f deployment.yaml` sends your manifest to the API server. `kubectl get pods` asks the API server for the current pod list. `kubectl logs my-pod` streams logs from the kubelet on whichever node that pod is running.

To use `kubectl`, it needs to know which cluster to talk to — this is configured in `~/.kube/config`. When you use a managed cluster, the cloud provider's CLI typically writes the right config for you (`aws eks update-kubeconfig`, `gcloud container clusters get-credentials`).

## Running locally first

Before running Kubernetes in production, run it on your laptop. The two most common tools:

- **kind** (Kubernetes IN Docker) — runs a full cluster using Docker containers as nodes. Lightweight, fast to start, great for CI and local development.
- **minikube** — starts a VM or container with a single-node cluster. Slightly heavier but has built-in addons for common tools.

Both give you a real Kubernetes cluster locally. Start with kind — it's the faster path to "I have a working cluster."

<!-- RESOURCES -->

- [Kubernetes Documentation - What is Kubernetes](https://kubernetes.io/docs/concepts/overview/) -- type: docs, time: 20m
- [How Kubernetes runs pods under the hood](https://blog.esc.sh/kubernetes-containers-linux-processes/) -- type: docs, time: 10m
- [A dumb container orchestration tool](https://github.com/MansoorMajeed/Dubernetes) -- type: tool, time: 10m
- [kind - Kubernetes in Docker](https://kind.sigs.k8s.io/) -- type: tool, time: 15m
- [minikube - Run Kubernetes Locally](https://minikube.sigs.k8s.io/docs/start/) -- type: tool, time: 15m
- [The Illustrated Children's Guide to Kubernetes](https://www.cncf.io/phippy/the-childrens-illustrated-guide-to-kubernetes/) -- type: article, time: 15m
- [Kubernetes the Hard Way (Kelsey Hightower)](https://github.com/kelseyhightower/kubernetes-the-hard-way) -- type: tutorial, time: 4h

<!-- ZH_SUMMARY -->
在生产环境中运行容器意味着要回答一些棘手的问题：这个容器应该放在哪台服务器上？它崩溃了怎么办？如何在不中断流量的情况下发布新版本？Kubernetes 正是能回答所有这些问题的系统——并且已成为大规模运行容器的事实标准。

<!-- ZH_DEEP_DIVE -->
## Kubernetes 解决的问题

Docker Compose 在一台机器上运行容器。对于单台服务器来说这没问题，但生产系统面临更棘手的问题。你需要容器在机器故障时仍能存活。你需要在流量高峰时运行更多容器，在流量低谷时运行更少容器。你需要在不中断服务的情况下发布新版本。你需要在容器崩溃时重启它们。必须有人——或者某个东西——来协调这一切。

这个协调者被称为**编排器（orchestrator）**。Kubernetes 是其中的主导者。它诞生于 Google 内部（那里有一个类似的内部系统 Borg 已运行多年），于 2014 年开源，并迅速成为标准，以至于云厂商基本上必须将其作为托管服务提供。如今，“容器编排”和“Kubernetes”几乎成了同义词。

## Kubernetes 实际做了什么

Kubernetes 在一个机器集群上运行你的容器，并持续工作以使集群与你声明的状态保持一致。你不会说“在服务器 3 上运行这个容器”。你会说“我想要这个容器运行 5 个副本，每个至少 500MB 内存”。Kubernetes 会选择服务器、启动容器，如果某个容器崩溃，会自动替换它。如果某台服务器宕机，该服务器上的工作负载会被重新调度到健康的服务器上。

这种模型——声明期望状态，让系统调和现实以与之匹配——正是 Kubernetes 强大的原因。也正是它大部分复杂性的来源。

## 控制平面与工作节点

一个 Kubernetes 集群分为两部分：

- **控制平面（Control plane）**——大脑。运行 API server、scheduler、controller manager 和 etcd（集群的键值存储）。控制平面做出决策：将 Pod 调度到哪里、何时替换失败的 Pod、如何滚动发布更新。
- **工作节点（Worker nodes）**——肌肉。这些是实际运行你容器的机器。每个节点运行 `kubelet`（与控制平面通信）、`kube-proxy`（处理网络）以及容器运行时（通常是 containerd）。

当你使用 EKS、GKE 或 AKS 这样的托管 Kubernetes 服务时，云厂商为你运行控制平面。你管理工作节点——或者通过托管节点组让厂商也管理这些节点。

## kubectl——控制平面的接口

你用 Kubernetes 做的一切都通过 `kubectl` 进行，这是与 Kubernetes API server 通信的命令行工具。`kubectl apply -f deployment.yaml` 将你的清单发送到 API server。`kubectl get pods` 向 API server 请求当前的 Pod 列表。`kubectl logs my-pod` 从该 Pod 所在节点上的 kubelet 流式获取日志。

要使用 `kubectl`，它需要知道与哪个集群通信——这在 `~/.kube/config` 中配置。当你使用托管集群时，云厂商的 CLI 通常会为你写入正确的配置（`aws eks update-kubeconfig`、`gcloud container clusters get-credentials`）。

## 先在本地运行

在生产环境运行 Kubernetes 之前，先在你的笔记本电脑上运行它。两个最常见的工具：

- **kind**（Kubernetes IN Docker）——使用 Docker 容器作为节点运行完整集群。轻量、启动快，非常适合 CI 和本地开发。
- **minikube**——启动一个 VM 或容器，运行单节点集群。稍重一些，但内置了常用工具的插件。

两者都能在本地为你提供一个真正的 Kubernetes 集群。从 kind 开始——它是通往“我有一个可用集群”的更快路径。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - 什么是 Kubernetes](https://kubernetes.io/docs/concepts/overview/) -- 类型：文档，时长：20m
- [Kubernetes 如何在底层运行 Pod](https://blog.esc.sh/kubernetes-containers-linux-processes/) -- 类型：文档，时长：10m
- [一个简易的容器编排工具](https://github.com/MansoorMajeed/Dubernetes) -- 类型：工具，时长：10m
- [kind - Docker 中的 Kubernetes](https://kind.sigs.k8s.io/) -- 类型：工具，时长：15m
- [minikube - 在本地运行 Kubernetes](https://minikube.sigs.k8s.io/docs/start/) -- 类型：工具，时长：15m
- [Kubernetes 儿童图解指南](https://www.cncf.io/phippy/the-childrens-illustrated-guide-to-kubernetes/) -- 类型：文章，时长：15m
- [Kubernetes the Hard Way（Kelsey Hightower）](https://github.com/kelseyhightower/kubernetes-the-hard-way) -- 类型：教程，时长：4h

<!-- ZH_UI -->
1. 解释 Kubernetes 解决了哪些仅靠 Docker Compose 无法解决的问题
2. 理解控制平面与工作节点的区别
3. 了解 kubectl 是什么以及如何将其连接到集群
4. 使用 kind 或 minikube 运行本地集群
5. Kubernetes 说得通。但我到底怎么在上面运行一个容器？
6. 好，我想在这个集群上运行我的容器。我懂 Docker，我知道 docker run——但在 Kubernetes 里怎么做等价的事？kubectl run？一个 YAML 文件？还有文档里老出现的这个“Pod”到底是什么——它只是容器的一个花哨说法吗？
7. 在我运行任何东西之前——Kubernetes 如何防止不同团队、应用和环境互相干扰？
8. 如果预发和生产都跑在同一个集群上，队友们也在部署他们的东西——是什么阻止一切搅在一起？在变成一团乱之前，我需要某种隔离。
