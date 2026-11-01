---
id: troubleshooting-basics
title: 'Troubleshooting: When Things Break'
zone: running
edges:
  to:
    - id: running-your-store
      question: >-
        I know how to debug my setup. How do I put everything together and run
        my real app?
      detail: >-
        I can debug each part of the stack in isolation now. But I've never
        assembled a complete deployment from scratch — server, code, process
        manager, web server, TLS, domain — all of it together. What does that
        actually look like end to end?
difficulty: 2
tags:
  - troubleshooting
  - debugging
  - curl
  - ss
  - systemctl
  - nginx
  - '502'
  - connection-refused
category: practice
milestones:
  - Use a systematic checklist to diagnose why a web app is not responding
  - >-
    Distinguish between a 502 Bad Gateway and a Connection Refused error and
    know what causes each
  - 'Test each layer independently: app, Nginx, firewall, DNS'
title_zh: "故障排查：当系统出现故障时"

---


Something is broken. Your site is not loading. You are getting 502 errors. The app crashed and did not come back. The page loads but CSS is missing.

The difference between a junior engineer and a senior one is not that the senior never encounters these problems. It is that the senior has a systematic approach for finding the problem instead of randomly changing things and hoping something works.

This is that approach.

<!-- DEEP_DIVE -->

**The golden rule: isolate each layer**

Your stack has multiple layers, and the problem is in exactly one of them. Test each layer independently to find which one:

```
Browser / curl request
    ↓ DNS resolves domain to IP
    ↓ Firewall: is port 80/443 open?
    ↓ Nginx: is it running? is config correct?
    ↓ App: is it running? is it listening on the right port?
    ↓ App logic: did the code throw an exception?
```

Work top-down or bottom-up, but check each layer in isolation.

**The diagnostic checklist**

**Step 1: Is the process running?**

```bash
# Check your app
sudo systemctl status mystore
# Look for: Active: active (running)
# If it says "failed" or "inactive", your app is not running

# Check Nginx
sudo systemctl status nginx
```

If the service is not running, check why it failed:
```bash
sudo journalctl -u mystore -n 50
# The last few lines will tell you why it crashed or failed to start
```

**Step 2: Is it listening on the expected port?**

```bash
sudo ss -tlnp | grep LISTEN
# Look for your app on 127.0.0.1:5000 (or whatever port)
# Look for Nginx on 0.0.0.0:80 and 0.0.0.0:443
```

If your app is running but not listening, the `ExecStart` command may be wrong (wrong path, wrong port) or the app crashed after starting.

**Step 3: Can you reach the app locally?**

```bash
# Test your app directly, bypassing Nginx
curl http://127.0.0.1:5000/

# If you get a response: the app is working, problem is in Nginx or above
# If you get "Connection refused": the app is not listening on that port
# If the request hangs: the app is listening but not responding (deadlock, overload)
```

**Step 4: Can Nginx reach the app?**

```bash
# Check Nginx config syntax
sudo nginx -t
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# Check Nginx error log
sudo tail -20 /var/log/nginx/error.log

# Common Nginx errors:
# "connect() failed (111: Connection refused)" → app is not listening
# "no live upstreams" → app crashed
# "502 Bad Gateway" → Nginx can't talk to your app
```

**Step 5: Is the firewall the problem?**

```bash
# Check ufw rules
sudo ufw status

# Test from your laptop — does port 80 respond?
curl -v http://YOUR_SERVER_IP/
# If it hangs with no response: firewall is blocking it
# If you get a response: firewall is fine
```

**Common problems and their fixes**

**502 Bad Gateway**
```
Nginx is running, but cannot reach your app.
```
Fix: check if your app is running (`systemctl status`), check if it is listening on the port Nginx expects (`ss -tlnp`), check your Nginx `proxy_pass` port matches your app's port.

**Connection refused**
```
Nothing is listening on that port.
```
Fix: start your service (`systemctl start`), check the service logs to see why it is not running.

**403 Forbidden**
```
Nginx found the file/directory but does not have permission to read it.
```
Fix: check file ownership and permissions. Nginx runs as `www-data` user. Static files should be readable by `www-data`.

**App works locally but not through domain**
```
curl http://127.0.0.1:5000/ works
curl http://YOUR_DOMAIN/ does not
```
Fix: check DNS (has the record propagated?), check Nginx server_name matches your domain, check TLS cert is valid.

**App was working, now it is not (after code deploy)**
```
You deployed new code and the app stopped working.
```
Checklist:
- Did you restart the service? (`sudo systemctl restart mystore`)
- Did you install new dependencies? (`pip install -r requirements.txt`)
- Did the new code have a syntax error? (check `journalctl -u mystore -n 20`)
- Did an environment variable change?

**Debugging tool cheat sheet**

```bash
# Is the service running?
sudo systemctl status mystore
sudo systemctl status nginx

# What is listening?
sudo ss -tlnp

# Reach the app directly
curl http://127.0.0.1:5000/
curl -I http://127.0.0.1:5000/    # Just headers

# App logs
sudo journalctl -u mystore -f
sudo journalctl -u mystore -n 50

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Test Nginx config
sudo nginx -t

# Firewall status
sudo ufw status verbose

# Disk space (full disk causes mysterious failures)
df -h

# Memory (out of memory kills processes)
free -h

# What processes are consuming most resources
htop
```

**The mindset**

Do not randomly restart things hoping something fixes itself. Do not change multiple things at once. Change one thing, test it, then change the next.

When you find the problem, understand *why* it happened so you can prevent it. "The process crashed" is not an explanation. "The process crashed because it ran out of memory when loading a 2 GB CSV into RAM" is.

<!-- RESOURCES -->

- [DigitalOcean - Nginx Troubleshooting](https://www.digitalocean.com/community/tutorials/how-to-troubleshoot-common-nginx-errors) -- type: tutorial, time: 20m
- [ss command reference](https://man7.org/linux/man-pages/man8/ss.8.html) -- type: reference, time: 10m

<!-- ZH_SUMMARY -->
出问题了。你的网站无法加载。你遇到了 502 错误。应用崩溃了，而且没有恢复。页面能加载，但 CSS 丢失了。

初级工程师和资深工程师的区别，不在于资深工程师从不遇到这些问题。而在于资深工程师有一套系统化的方法来定位问题，而不是随意改动、寄希望于某处能生效。

这就是那套方法。

<!-- ZH_DEEP_DIVE -->
**黄金法则：隔离每一层**

你的栈有多个层次，问题恰好出在其中某一层。独立测试每一层，找出问题所在：

```
Browser / curl request
    ↓ DNS resolves domain to IP
    ↓ Firewall: is port 80/443 open?
    ↓ Nginx: is it running? is config correct?
    ↓ App: is it running? is it listening on the right port?
    ↓ App logic: did the code throw an exception?
```

自上而下或自下而上都可以，但要隔离检查每一层。

**诊断清单**

**第 1 步：进程在运行吗？**

```bash
# Check your app
sudo systemctl status mystore
# Look for: Active: active (running)
# If it says "failed" or "inactive", your app is not running

# Check Nginx
sudo systemctl status nginx
```

如果服务没有运行，检查失败原因：
```bash
sudo journalctl -u mystore -n 50
# The last few lines will tell you why it crashed or failed to start
```

**第 2 步：它在预期的端口上监听吗？**

```bash
sudo ss -tlnp | grep LISTEN
# Look for your app on 127.0.0.1:5000 (or whatever port)
# Look for Nginx on 0.0.0.0:80 and 0.0.0.0:443
```

如果你的应用在运行但没有监听，可能是 `ExecStart` 命令有误（路径错误、端口错误），或者应用启动后崩溃了。

**第 3 步：能在本地访问应用吗？**

```bash
# Test your app directly, bypassing Nginx
curl http://127.0.0.1:5000/

# If you get a response: the app is working, problem is in Nginx or above
# If you get "Connection refused": the app is not listening on that port
# If the request hangs: the app is listening but not responding (deadlock, overload)
```

**第 4 步：Nginx 能访问到应用吗？**

```bash
# Check Nginx config syntax
sudo nginx -t
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# Check Nginx error log
sudo tail -20 /var/log/nginx/error.log

# Common Nginx errors:
# "connect() failed (111: Connection refused)" → app is not listening
# "no live upstreams" → app crashed
# "502 Bad Gateway" → Nginx can't talk to your app
```

**第 5 步：是防火墙的问题吗？**

```bash
# Check ufw rules
sudo ufw status

# Test from your laptop — does port 80 respond?
curl -v http://YOUR_SERVER_IP/
# If it hangs with no response: firewall is blocking it
# If you get a response: firewall is fine
```

**常见问题及其修复方法**

**502 Bad Gateway**
```
Nginx is running, but cannot reach your app.
```
修复：检查应用是否在运行（`systemctl status`），检查它是否在 Nginx 预期的端口上监听（`ss -tlnp`），检查 Nginx 的 `proxy_pass` 端口是否与应用端口一致。

**Connection refused**
```
Nothing is listening on that port.
```
修复：启动服务（`systemctl start`），查看服务日志了解它为什么没有运行。

**403 Forbidden**
```
Nginx found the file/directory but does not have permission to read it.
```
修复：检查文件所有权和权限。Nginx 以 `www-data` 用户运行。静态文件应可被 `www-data` 读取。

**应用本地可用，但通过域名不可用**
```
curl http://127.0.0.1:5000/ works
curl http://YOUR_DOMAIN/ does not
```
修复：检查 DNS（记录是否已传播？），检查 Nginx 的 server_name 是否与你的域名匹配，检查 TLS 证书是否有效。

**应用之前正常，现在不正常了（代码部署之后）**
```
You deployed new code and the app stopped working.
```
检查清单：
- 你重启服务了吗？（`sudo systemctl restart mystore`）
- 你安装新依赖了吗？（`pip install -r requirements.txt`）
- 新代码有语法错误吗？（检查 `journalctl -u mystore -n 20`）
- 环境变量有变化吗？

**调试工具速查表**

```bash
# Is the service running?
sudo systemctl status mystore
sudo systemctl status nginx

# What is listening?
sudo ss -tlnp

# Reach the app directly
curl http://127.0.0.1:5000/
curl -I http://127.0.0.1:5000/    # Just headers

# App logs
sudo journalctl -u mystore -f
sudo journalctl -u mystore -n 50

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Test Nginx config
sudo nginx -t

# Firewall status
sudo ufw status verbose

# Disk space (full disk causes mysterious failures)
df -h

# Memory (out of memory kills processes)
free -h

# What processes are consuming most resources
htop
```

**思维方式**

不要随意重启，指望问题自己消失。不要同时改动多个地方。一次只改一处，测试后再改下一处。

找到问题后，要理解它*为什么*发生，这样才能预防。 “进程崩溃了”不是解释。“进程崩溃是因为它在把 2 GB 的 CSV 加载到内存时耗尽了内存”才是。

<!-- ZH_RESOURCES -->
- [DigitalOcean - Nginx 故障排查](https://www.digitalocean.com/community/tutorials/how-to-troubleshoot-common-nginx-errors) -- 类型: 教程, 时长: 20m
- [ss 命令参考](https://man7.org/linux/man-pages/man8/ss.8.html) -- 类型: 参考, 时长: 10m

<!-- ZH_UI -->
1. 使用系统性检查清单诊断 Web 应用无响应的原因
2. 区分 502 Bad Gateway 与 Connection Refused 错误，并了解各自的成因
3. 独立测试每一层：应用、Nginx、防火墙、DNS
4. 我知道如何调试我的配置。如何把所有部分整合起来并运行我的真实应用？
5. 我现在能独立调试技术栈的每个部分。但我从未从零搭建过完整部署——服务器、代码、进程管理器、Web 服务器、TLS、域名——全部整合在一起。这端到端实际是什么样子？
