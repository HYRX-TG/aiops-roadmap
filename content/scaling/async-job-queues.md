---
id: async-job-queues
title: Async Job Queues
zone: scaling
edges:
  to: []
difficulty: 2
tags:
  - queues
  - async
  - background-workers
  - sqs
  - rabbitmq
  - celery
  - message-queue
  - job-queue
  - scaling
category: concept
milestones:
  - Explain why doing slow work synchronously in a web request is a problem at scale
  - Know what a message queue is and what SQS and RabbitMQ are
  - Explain the producer/consumer pattern
  - Know what a Celery worker is and how it connects to a broker
  - Explain what at-least-once delivery means and why idempotency matters
  - Know what a dead-letter queue is and why every queue needs one
title_zh: "异步任务队列"

---


Some work doesn't belong in the HTTP request path. Sending a confirmation email, resizing an uploaded image, generating a PDF invoice, syncing to an external API — these are slow, often unreliable, and the user doesn't need to wait for them to finish before getting a response. Async job queues let you hand off slow work to background workers, respond immediately to the user, and process the work independently.

<!-- DEEP_DIVE -->

## The problem with synchronous slow work

In a synchronous request handler, every line of code runs before the HTTP response is sent. If sending an email takes 500ms and your web framework handles 100 concurrent requests, 100 workers might each be blocked waiting on email delivery simultaneously. A transient email service outage makes your entire web tier slow.

The pattern breaks in other ways too: if the request fails halfway through (network timeout, process killed), the slow operation might complete partially or not at all, leaving your system in an inconsistent state. You have no retry logic, no visibility into what's happening.

## The producer-consumer pattern

An async job queue introduces two roles:

- **Producer**: the web application. When a user completes checkout, the producer adds a job to the queue: "send confirmation email for order #12345." It does this in milliseconds, then returns the HTTP response to the user.
- **Consumer** (worker): a separate process that reads jobs from the queue and executes them. Workers run independently of the web tier and can be scaled separately.

```python
# Producer: in the checkout view (web process)
from tasks import send_confirmation_email
send_confirmation_email.delay(order_id=order.id)  # enqueues, returns immediately
return redirect("/order/confirmed")

# Consumer: in tasks.py (worker process)
@celery_app.task(bind=True, max_retries=3)
def send_confirmation_email(self, order_id):
    order = Order.objects.get(id=order_id)
    email.send(order.user.email, ...)  # the actual slow work
```

## Message queues: SQS, RabbitMQ

The queue is the communication channel between producers and consumers. Messages are placed in the queue by producers and consumed (and deleted) by consumers.

**SQS (AWS Simple Queue Service)**: a fully managed, serverless queue. Extremely simple to operate — no servers to manage, virtually unlimited scale. Supports standard queues (at-least-once delivery, best-effort ordering) and FIFO queues (exactly-once delivery, strict ordering). The default visibility timeout determines how long a consumed message is hidden from other consumers while being processed.

**RabbitMQ**: a self-hosted (or CloudAMQP-hosted) message broker. More powerful routing (exchanges, topic routing), better suited for complex publish/subscribe patterns. Requires operational effort to run. Use SQS if your patterns are simple enough to fit; reach for RabbitMQ when you need complex routing.

## Celery: Python's worker framework

Celery is the standard Python library for defining and executing background tasks. Workers connect to a broker (SQS, Redis, or RabbitMQ), read tasks, execute them, and report results.

Key Celery concepts:
- **Task**: a Python function decorated with `@celery_app.task`
- **Broker**: where tasks are queued (Redis is common for development; SQS for production)
- **Worker**: a process running `celery worker`, consuming tasks from the broker

Start workers with `celery worker -A myapp.celery -c 4` (4 concurrent workers per process).

## At-least-once delivery and idempotency

SQS guarantees **at-least-once delivery** — in rare cases (worker crashes mid-processing), a message may be delivered and processed more than once. If your task is "charge the customer," running it twice is a serious bug.

Design tasks to be **idempotent**: running them multiple times has the same effect as running them once. For a charge, check whether the payment already exists before creating it. For a confirmation email, track whether you've already sent it and skip if so.

## Dead-letter queues

When a task fails repeatedly (exceptions, timeouts), it shouldn't stay in the main queue forever. Configure a **dead-letter queue (DLQ)**: after a task fails N times, SQS moves it to the DLQ. Your monitoring watches the DLQ — items there need human review. Without a DLQ, failed tasks either retry forever (consuming worker capacity) or are silently dropped.

<!-- RESOURCES -->

- [AWS SQS Documentation](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) -- type: docs, time: 20m
- [Celery Documentation - Getting Started](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) -- type: docs, time: 30m
- [SQS Dead-Letter Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) -- type: docs, time: 10m

<!-- ZH_SUMMARY -->
有些工作不适合放在 HTTP 请求路径中处理。发送确认邮件、调整上传图片的尺寸、生成 PDF 发票、同步到外部 API——这些操作缓慢且往往不可靠，用户也不需要等它们完成才能收到响应。异步任务队列让你可以把慢速工作交给后台 worker 处理，立即响应用户，并独立处理这些工作。

<!-- ZH_DEEP_DIVE -->
## 同步慢任务的问题

在同步请求处理器中，每一行代码都在 HTTP 响应发送之前执行。如果发送一封邮件需要 500ms，而你的 Web 框架处理 100 个并发请求，那么 100 个 worker 可能同时被阻塞在等待邮件投递上。一次短暂的邮件服务故障就会让整个 Web 层变慢。

这种模式在其他方面也会出问题：如果请求执行到一半失败（网络超时、进程被杀），慢操作可能部分完成或完全未完成，使系统处于不一致状态。你既没有重试逻辑，也无法观测正在发生什么。

## 生产者-消费者模式

异步任务队列引入了两种角色：

- **生产者（Producer）**：Web 应用。当用户完成结账时，生产者向队列添加一个任务："为订单 #12345 发送确认邮件。" 它在毫秒级完成这一操作，然后把 HTTP 响应返回给用户。
- **消费者（Consumer，即 worker）**：一个独立进程，从队列读取任务并执行。Worker 独立于 Web 层运行，可以单独扩缩容。

```python
# Producer: in the checkout view (web process)
from tasks import send_confirmation_email
send_confirmation_email.delay(order_id=order.id)  # enqueues, returns immediately
return redirect("/order/confirmed")

# Consumer: in tasks.py (worker process)
@celery_app.task(bind=True, max_retries=3)
def send_confirmation_email(self, order_id):
    order = Order.objects.get(id=order_id)
    email.send(order.user.email, ...)  # the actual slow work
```

## 消息队列：SQS、RabbitMQ

队列是生产者与消费者之间的通信通道。生产者把消息放入队列，消费者消费（并删除）消息。

**SQS（AWS Simple Queue Service）**：全托管、Serverless 的队列。运维极其简单——无需管理服务器，几乎无限扩展。支持标准队列（至少一次投递、尽力排序）和 FIFO 队列（精确一次投递、严格排序）。默认的可见性超时（visibility timeout）决定了被消费的消息在处理期间对其他消费者隐藏多久。

**RabbitMQ**：自托管（或 CloudAMQP 托管）的消息代理。路由能力更强（exchange、topic 路由），更适合复杂的发布/订阅模式。需要投入运维工作。如果你的模式足够简单、能满足需求，就用 SQS；当你需要复杂路由时，再选择 RabbitMQ。

## Celery：Python 的 worker 框架

Celery 是用于定义和执行后台任务的标准 Python 库。Worker 连接到 broker（SQS、Redis 或 RabbitMQ），读取任务、执行任务并上报结果。

Celery 的关键概念：
- **Task**：用 `@celery_app.task` 装饰的 Python 函数
- **Broker**：任务排队的地方（开发环境常用 Redis；生产环境用 SQS）
- **Worker**：运行 `celery worker` 的进程，从 broker 消费任务

用 `celery worker -A myapp.celery -c 4` 启动 worker（每个进程 4 个并发 worker）。

## 至少一次投递与幂等性

SQS 保证**至少一次投递**——在少数情况下（worker 在处理中途崩溃），一条消息可能被投递并处理多次。如果你的任务是"向客户扣款"，运行两次就是严重的 bug。

把任务设计成**幂等**的：多次运行与运行一次效果相同。对于扣款，在创建支付之前先检查支付是否已存在。对于确认邮件，跟踪是否已经发送过，如果已发送就跳过。

## 死信队列

当任务反复失败（异常、超时）时，它不应永远留在主队列中。配置一个**死信队列（DLQ）**：任务失败 N 次后，SQS 将其移入 DLQ。你的监控关注 DLQ——其中的条目需要人工审查。没有 DLQ 的话，失败的任务要么永远重试（消耗 worker 容量），要么被静默丢弃。

<!-- ZH_RESOURCES -->
- [AWS SQS 文档](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) -- 类型: 文档, 时间: 20m
- [Celery 文档 - 入门](https://docs.celeryq.dev/en/stable/getting-started/introduction.html) -- 类型: 文档, 时间: 30m
- [SQS 死信队列](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) -- 类型: 文档, 时间: 10m

<!-- ZH_UI -->
1. 解释为什么在 Web 请求中同步执行慢速任务在规模化时会成为问题
2. 了解什么是消息队列，以及 SQS 和 RabbitMQ 是什么
3. 解释生产者/消费者模式
4. 了解什么是 Celery worker，以及它如何连接 broker
5. 解释至少一次投递的含义，以及为什么幂等性很重要
6. 了解什么是死信队列，以及为什么每个队列都需要一个
