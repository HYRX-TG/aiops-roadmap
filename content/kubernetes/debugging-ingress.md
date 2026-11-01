---
id: debugging-ingress
title: Debugging Ingress
zone: kubernetes
edges:
  to: []
difficulty: 2
tags:
  - kubernetes
  - debugging
  - ingress
  - nginx
  - "404"
  - "502"
  - tls
  - k8s
category: practice
milestones:
  - >-
    Distinguish between a 404 (ingress can't find a matching rule or service)
    and a 502 (found the service but upstream is failing)
  - Use kubectl describe ingress to verify rules, host, and backend service
  - Check ingress controller logs to see what it's actually doing
  - >-
    Confirm the backend Service name and port in the Ingress spec exactly match
    the real Service
title_zh: "调试 Ingress"

---


Ingress failures usually fall into two categories: the ingress controller can't find a rule matching your request (404), or it found the rule and the backend service is rejecting traffic (502/503). Each points to a different place to look.

<!-- DEEP_DIVE -->

## 404 vs 502 — read the error first

**404 Not Found** — the ingress controller received the request but couldn't match it to any rule. Either the hostname doesn't match, the path doesn't match, or the Ingress resource itself isn't being picked up by the controller.

**502 Bad Gateway** — the ingress controller matched the rule and forwarded the request, but the backend pod or service returned an error or didn't respond. The upstream is failing, not the ingress routing.

**503 Service Unavailable** — similar to 502; often means the backend service has no healthy endpoints (no pods behind it).

## Inspect the Ingress resource

```bash
kubectl describe ingress my-ingress
```

Check:
- **Rules** — does the hostname match exactly what you're requesting? `www.example.com` and `example.com` are different.
- **Backend service name and port** — do they match a real Service in the same namespace?
- **TLS** — if you configured TLS, does the secret name exist?

Also check that the Ingress has the right `ingressClassName` or annotation for your controller. A common mistake is applying an Ingress without specifying the class, and the controller ignores it entirely:

```yaml
spec:
  ingressClassName: nginx   # must match your installed controller
```

## Verify the backend Service exists and has endpoints

The Ingress routes to a Service by name. Confirm that Service actually exists and has pods behind it:

```bash
kubectl get service my-service
kubectl get endpoints my-service
```

If `endpoints` shows `<none>`, the Service has no pods — the Ingress will correctly receive the request and correctly return 502/503 because there's nothing to forward it to. Fix the Service first (this is a Services problem, not an Ingress problem).

## Check the ingress controller logs

The ingress controller (nginx, Traefik, etc.) logs what it's doing. Find the controller pod:

```bash
kubectl get pods -n ingress-nginx
```

Then check its logs:

```bash
kubectl logs -n ingress-nginx deploy/ingress-nginx-controller
```

For nginx-ingress, you'll see access logs and error logs. If it's rejecting requests, misconfiguring upstream, or failing TLS negotiation, it's in here.

## TLS issues

If HTTPS isn't working:

```bash
kubectl describe certificate my-tls-cert      # if using cert-manager
kubectl get certificaterequest -n default
```

cert-manager certificate objects go through states: `False` → `True` (issued). If it's stuck in `False`, describe the certificate for the reason. Common causes: wrong DNS name, ACME challenge failing (the domain isn't pointing at your cluster yet), or rate limits from Let's Encrypt.

You can also check whether the TLS secret actually exists:

```bash
kubectl get secret my-tls-secret
```

If the secret doesn't exist, the ingress controller will typically serve a self-signed fallback cert and the browser will show a certificate warning.

## A systematic approach

1. Read the error: 404 (routing problem) or 502/503 (backend problem)?
2. `kubectl describe ingress` — check host, path rules, backend service name and port, ingressClassName
3. `kubectl get endpoints my-service` — does the backend have pods?
4. Check the ingress controller pod logs for errors
5. For TLS: `kubectl describe certificate` or check the TLS secret exists

<!-- RESOURCES -->

- [Kubernetes Docs - Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) -- type: docs, time: 20m
- [nginx-ingress Troubleshooting Guide](https://kubernetes.github.io/ingress-nginx/troubleshooting/) -- type: docs, time: 15m

<!-- ZH_SUMMARY -->
Ingress 故障通常分为两类：ingress controller 找不到与你的请求匹配的规则（404），或者找到了规则但后端服务拒绝流量（502/503）。这两类故障指向不同的排查位置。

<!-- ZH_DEEP_DIVE -->
## 404 与 502 — 先读懂错误信息

**404 Not Found** — ingress 控制器收到了请求，但无法将其匹配到任何规则。可能是主机名不匹配、路径不匹配，或者 Ingress 资源本身没有被控制器识别。

**502 Bad Gateway** — ingress 控制器匹配到了规则并转发了请求，但后端 pod 或 service 返回了错误或没有响应。问题出在上游，而不是 ingress 路由。

**503 Service Unavailable** — 与 502 类似；通常意味着后端 service 没有健康的 endpoints（其后面没有 pod）。

## 检查 Ingress 资源

```bash
kubectl describe ingress my-ingress
```

检查：
- **规则** — 主机名是否与你请求的完全一致？`www.example.com` 和 `example.com` 是不同的。
- **后端 service 名称和端口** — 它们是否匹配同一命名空间中真实存在的 Service？
- **TLS** — 如果你配置了 TLS，secret 名称是否存在？

还要检查 Ingress 是否具有适用于你的控制器的正确 `ingressClassName` 或注解。一个常见错误是应用 Ingress 时未指定 class，导致控制器完全忽略它：

```yaml
spec:
  ingressClassName: nginx   # 必须与你安装的控制器匹配
```

## 验证后端 Service 存在且有 endpoints

Ingress 按名称将请求路由到 Service。确认该 Service 确实存在，并且其后面有 pod：

```bash
kubectl get service my-service
kubectl get endpoints my-service
```

如果 `endpoints` 显示 `<none>`，说明该 Service 没有 pod — Ingress 会正确地接收请求并正确地返回 502/503，因为没有可转发到的目标。请先修复 Service（这是 Service 的问题，不是 Ingress 的问题）。

## 检查 ingress 控制器日志

ingress 控制器（nginx、Traefik 等）会记录其操作。找到控制器 pod：

```bash
kubectl get pods -n ingress-nginx
```

然后检查其日志：

```bash
kubectl logs -n ingress-nginx deploy/ingress-nginx-controller
```

对于 nginx-ingress，你会看到访问日志和错误日志。如果它拒绝请求、错误配置上游或 TLS 协商失败，相关信息都在这里。

## TLS 问题

如果 HTTPS 无法正常工作：

```bash
kubectl describe certificate my-tls-cert      # 如果使用 cert-manager
kubectl get certificaterequest -n default
```

cert-manager 的 certificate 对象会经历多个状态：`False` → `True`（已签发）。如果卡在 `False`，请 describe 该 certificate 以查看原因。常见原因：DNS 名称错误、ACME challenge 失败（域名尚未指向你的集群），或 Let's Encrypt 的速率限制。

你还可以检查 TLS secret 是否实际存在：

```bash
kubectl get secret my-tls-secret
```

如果 secret 不存在，ingress 控制器通常会提供一个自签名的备用证书，浏览器会显示证书警告。

## 系统化的排查方法

1. 读懂错误：404（路由问题）还是 502/503（后端问题）？
2. `kubectl describe ingress` — 检查 host、路径规则、后端 service 名称和端口、ingressClassName
3. `kubectl get endpoints my-service` — 后端是否有 pod？
4. 检查 ingress 控制器 pod 日志中的错误
5. 对于 TLS：`kubectl describe certificate` 或检查 TLS secret 是否存在

<!-- ZH_RESOURCES -->
- [Kubernetes 文档 - Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) -- 类型：文档，时长：20m
- [nginx-ingress 故障排查指南](https://kubernetes.github.io/ingress-nginx/troubleshooting/) -- 类型：文档，时长：15m

<!-- ZH_UI -->
1. 区分 404（Ingress 找不到匹配的规则或 Service）与 502（找到了 Service，但上游失败）
2. 使用 kubectl describe ingress 验证规则、host 和后端 Service
3. 查看 Ingress Controller 日志，了解其实际行为
4. 确认 Ingress spec 中的后端 Service 名称和端口与真实 Service 完全一致
