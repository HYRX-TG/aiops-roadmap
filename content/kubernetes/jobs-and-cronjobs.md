---
id: jobs-and-cronjobs
title: Jobs and CronJobs
zone: kubernetes
edges:
  to: []
difficulty: 1
tags:
  - kubernetes
  - jobs
  - cronjobs
  - batch
  - scheduling
  - migrations
  - k8s
category: concept
milestones:
  - Create a Job that runs a container to completion and verify it succeeded
  - 'Understand Job completion, parallelism, and backoff behaviour on failure'
  - Create a CronJob with a schedule expression and verify it runs on time
  - Run a database migration as a Job before a Deployment update
  - >-
    Explain the difference between a Job (run once) and a CronJob (run on
    schedule)
title_zh: "Jobs 和 CronJobs"

---


Deployments run workloads indefinitely and restart containers that exit. Jobs run a Pod to completion — once the container exits with code 0, the Job is done. CronJobs run Jobs on a schedule. Together they handle batch processing, database migrations, report generation, and any workload that runs once and stops.

<!-- DEEP_DIVE -->

## Jobs

A Job ensures a specified number of containers run to successful completion. Unlike a Deployment, it doesn't restart a successful container — it marks the Job complete and stops.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
spec:
  template:
    spec:
      restartPolicy: OnFailure    # or Never — Always is not allowed in Jobs
      containers:
        - name: migrate
          image: my-app:1.5
          command: ["python", "manage.py", "migrate"]
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: url
  backoffLimit: 4     # retry up to 4 times before marking the Job failed
```

Note: Pods in a Job must have `restartPolicy: OnFailure` or `restartPolicy: Never`. `Always` is not allowed — that's a Deployment concern.

## Checking Job status

```bash
kubectl get jobs
kubectl describe job db-migrate
kubectl logs job/db-migrate
```

A completed Job keeps its Pod around for log inspection. To clean up automatically after completion:

```yaml
spec:
  ttlSecondsAfterFinished: 300   # delete Job and its Pods 5 minutes after completion
```

## Parallel Jobs

For batch workloads that can be parallelized:

```yaml
spec:
  completions: 10    # run until 10 successful completions
  parallelism: 3     # run up to 3 Pods in parallel
```

Kubernetes runs up to 3 Pods simultaneously until 10 successful completions accumulate. Useful for processing a work queue, resizing images in a batch, or running test suites in parallel.

## CronJobs

A CronJob creates Jobs on a cron schedule:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-report
spec:
  schedule: "0 6 * * *"     # 6am UTC daily
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: report
              image: my-reports:latest
              command: ["python", "generate_report.py"]
  concurrencyPolicy: Forbid          # skip the new run if the previous is still running
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 5
```

Concurrency policies:
- **Allow** — multiple instances can run simultaneously (the default)
- **Forbid** — skip the scheduled run if the previous Job is still running
- **Replace** — terminate the running instance and start a fresh one

## Database migrations as Jobs

The cleanest pattern for database migrations in a Kubernetes workflow:

1. A Job runs the migration (`migrate up`) before the Deployment update
2. The Deployment only starts rolling out once the Job completes successfully

This is tricky to coordinate manually. With ArgoCD, you can use **resource hooks** — a Job annotated with `argocd.argoproj.io/hook: PreSync` runs before any other resources are applied. The sync only proceeds if the hook Job succeeds. Your migration Job and Deployment live in the same GitOps application, and every release automatically runs migrations before the Deployment rolls out.

<!-- RESOURCES -->

- [Kubernetes Docs - Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) -- type: docs, time: 20m
- [Kubernetes Docs - CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) -- type: docs, time: 15m
- [Crontab Guru - Cron Expression Editor](https://crontab.guru/) -- type: tool, time: 5m
- [ArgoCD Resource Hooks](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/) -- type: docs, time: 20m

<!-- ZH_SUMMARY -->
Deployment 无限期运行工作负载，并重启退出的容器。Job 运行 Pod 直至完成——一旦容器以退出码 0 退出，Job 即告完成。CronJob 按计划运行 Job。三者共同处理批处理、数据库迁移、报表生成，以及任何运行一次即停止的工作负载。

<!-- ZH_DEEP_DIVE -->
## Jobs

Job 确保指定数量的容器运行至成功完成。与 Deployment 不同，它不会重启已成功的容器——而是将 Job 标记为完成并停止。

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
spec:
  template:
    spec:
      restartPolicy: OnFailure    # 或 Never —— Jobs 中不允许使用 Always
      containers:
        - name: migrate
          image: my-app:1.5
          command: ["python", "manage.py", "migrate"]
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: url
  backoffLimit: 4     # 在将 Job 标记为失败之前最多重试 4 次
```

注意：Job 中的 Pod 必须设置 `restartPolicy: OnFailure` 或 `restartPolicy: Never`。不允许使用 `Always`——那是 Deployment 的职责。

## 检查 Job 状态

```bash
kubectl get jobs
kubectl describe job db-migrate
kubectl logs job/db-migrate
```

已完成的 Job 会保留其 Pod 以便检查日志。要在完成后自动清理：

```yaml
spec:
  ttlSecondsAfterFinished: 300   # 完成后 5 分钟删除 Job 及其 Pod
```

## 并行 Job

对于可以并行化的批处理工作负载：

```yaml
spec:
  completions: 10    # 运行直到累计 10 次成功完成
  parallelism: 3     # 最多并行运行 3 个 Pod
```

Kubernetes 会同时运行最多 3 个 Pod，直到累计 10 次成功完成。适用于处理工作队列、批量调整图片尺寸或并行运行测试套件。

## CronJob

CronJob 按照 cron 调度创建 Job：

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-report
spec:
  schedule: "0 6 * * *"     # 每天 UTC 时间 6 点
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: report
              image: my-reports:latest
              command: ["python", "generate_report.py"]
  concurrencyPolicy: Forbid          # 如果上一次运行仍在进行，则跳过本次运行
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 5
```

并发策略：
- **Allow** —— 多个实例可以同时运行（默认值）
- **Forbid** —— 如果上一次 Job 仍在运行，则跳过本次调度运行
- **Replace** —— 终止正在运行的实例并启动一个新实例

## 将数据库迁移作为 Job 运行

在 Kubernetes 工作流中执行数据库迁移最简洁的模式：

1. 在 Deployment 更新之前，由一个 Job 运行迁移（`migrate up`）
2. 只有 Job 成功完成后，Deployment 才开始滚动发布

手动协调这一点很棘手。使用 ArgoCD，你可以使用 **resource hooks**——一个带有 `argocd.argoproj.io/hook: PreSync` 注解的 Job 会在应用任何其他资源之前运行。只有该 hook Job 成功，同步才会继续。你的迁移 Job 和 Deployment 位于同一个 GitOps 应用中，每次发布都会在 Deployment 滚动发布之前自动运行迁移。

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) -- 类型: 文档, 时长: 20m
- [Kubernetes 文档 - CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) -- 类型: 文档, 时长: 15m
- [Crontab Guru - Cron 表达式编辑器](https://crontab.guru/) -- 类型: 工具, 时长: 5m
- [ArgoCD 资源钩子](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/) -- 类型: 文档, 时长: 20m

<!-- ZH_UI -->
1. 创建一个运行容器直至完成的 Job，并验证其成功
2. 理解 Job 的完成、并行性以及失败时的退避行为
3. 使用调度表达式创建 CronJob，并验证其按时运行
4. 在 Deployment 更新前，将数据库迁移作为 Job 运行
5. 解释 Job（运行一次）与 CronJob（按计划运行）的区别
