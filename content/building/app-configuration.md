---
id: app-configuration
title: Application Configuration
zone: building
edges:
  to:
    - id: it-works-on-my-laptop
      question: >-
        Config is separated from code now. But how do I get this running
        on an actual server instead of just my laptop?
      detail: >-
        My app reads config from environment variables, secrets are out of
        the source code, and I can switch between dev and production settings
        without changing any code. But it's still running on localhost. How
        do I actually deploy this thing?
difficulty: 1
tags:
  - configuration
  - environment-variables
  - twelve-factor
  - secrets
  - config-files
  - dotenv
category: concept
milestones:
  - Move hardcoded values (DB URLs, API keys) out of source code into environment variables
  - Understand the 12-factor app approach to configuration
  - Use a .env file for local development without committing it to git
  - Explain why config should change between environments but code should not
title_zh: "应用程序配置"

---


Your database password is in your source code. Your API key is on line 42 of `app.py`. The URL for your database is hardcoded to `localhost`. This works on your machine, but the moment you try to run this anywhere else — a server, a teammate's laptop, a CI pipeline — everything breaks because the config is wrong and it's baked into the code.

Application configuration is everything that changes between environments but shouldn't require a code change: database connection strings, API keys, feature flags, external service URLs, debug settings. The principle is simple: **config belongs in the environment, not in the code.**

<!-- DEEP_DIVE -->

## Why hardcoded config breaks things

When config is in your source code, you have a few bad options:

- **One codebase, one environment.** The code says `localhost:5432` so it only works on your laptop. To run it on a server you edit the code — and now your local version is broken.
- **Config files checked into git.** You have `config_dev.py` and `config_prod.py`. Someone commits a production database password to a public repo. You now have a security incident.
- **Branching for environments.** The `main` branch has production config, `dev` has dev config. Merging is a nightmare and someone will deploy dev config to production eventually.

All of these are symptoms of the same problem: config and code are tangled together.

## Environment variables

The standard solution is **environment variables**. Your app reads config from the environment at runtime:

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```

On your laptop, you set `DATABASE_URL=postgresql://localhost:5432/myapp`. On the server, it's `DATABASE_URL=postgresql://prod-db:5432/myapp`. Same code, different config. The app doesn't know or care where it's running.

For local development, a `.env` file (loaded by a library like `python-dotenv` or `dotenv` in Node) keeps your environment variables in one place without setting them globally. **This file goes in `.gitignore` — never commit it.**

## The 12-factor approach

The [12-factor app](https://12factor.net/config) methodology (written by Heroku's founders) codifies this as a principle: strict separation of config from code. Config is anything that varies between deploys — credentials, resource handles, per-deploy values. Code is everything else.

The test: could you open-source your codebase right now without compromising any credentials? If yes, your config separation is correct. If no, secrets are leaking into your code.

## Feature flags

Feature flags are config that controls behavior: `ENABLE_NEW_CHECKOUT=true`. They let you deploy code that isn't active yet, enable features for specific users, or kill a misbehaving feature without a redeploy. At small scale, environment variables work fine for this. At larger scale, dedicated feature flag services (LaunchDarkly, Unleash) give you runtime toggling without restarts.

<!-- RESOURCES -->

- [The Twelve-Factor App — Config](https://12factor.net/config) -- type: guide, time: 10m
- [python-dotenv documentation](https://saurabh-kumar.com/python-dotenv/) -- type: tool, time: 10m

<!-- ZH_SUMMARY -->
你的数据库密码就写在源代码里。你的 API key 在 `app.py` 的第 42 行。你的数据库 URL 被硬编码为 `localhost`。这在你的机器上能跑，但一旦你试图在别处运行它——服务器、队友的笔记本、CI 流水线——一切都会崩溃，因为配置是错的，而且它被固化在代码里。

应用配置指的是那些在不同环境之间会变化、但不应需要修改代码的东西：数据库连接字符串、API key、功能开关、外部服务 URL、调试设置。原则很简单：**配置属于环境，而不属于代码。**

<!-- ZH_DEEP_DIVE -->
## 为什么硬编码配置会出问题

当配置存在于源代码中时，你只有几个糟糕的选择：

- **一份代码库，一个环境。** 代码里写的是 `localhost:5432`，所以它只能在你自己的笔记本电脑上运行。要在服务器上运行就得改代码——而这样一来你本地的版本又坏了。
- **把配置文件提交到 git。** 你有 `config_dev.py` 和 `config_prod.py`。有人把生产数据库密码提交到了公开仓库。于是你就摊上安全事件了。
- **为不同环境开分支。** `main` 分支放生产配置，`dev` 分支放开发配置。合并简直是噩梦，而且迟早有人会把开发配置部署到生产环境。

这些都是同一个问题的症状：配置和代码纠缠在一起。

## 环境变量

标准解决方案是**环境变量**。你的应用在运行时从环境中读取配置：

```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```

在你的笔记本电脑上，你设置 `DATABASE_URL=postgresql://localhost:5432/myapp`。在服务器上，则是 `DATABASE_URL=postgresql://prod-db:5432/myapp`。同一份代码，不同的配置。应用既不知道也不关心自己运行在哪里。

对于本地开发，`.env` 文件（由 `python-dotenv` 或 Node 中的 `dotenv` 之类的库加载）可以把环境变量集中放在一处，而无需全局设置它们。**这个文件要放进 `.gitignore`——永远不要提交它。**

## 12-factor 方法

[12-factor app](https://12factor.net/config) 方法论（由 Heroku 的创始人编写）将这一点确立为一条原则：配置与代码严格分离。配置是任何在不同部署之间会变化的东西——凭据、资源句柄、每次部署特有的值。代码则是其余的一切。

检验方法：你现在能否在不泄露任何凭据的情况下将代码库开源？如果能，说明你的配置分离是正确的。如果不能，说明密钥正在泄漏进你的代码。

## 功能开关

功能开关是控制行为的配置：`ENABLE_NEW_CHECKOUT=true`。它们让你可以部署尚未启用的代码、为特定用户启用功能，或者在不重新部署的情况下关掉出问题的功能。在小规模场景下，环境变量就够用了。在更大规模下，专门的功能开关服务（LaunchDarkly、Unleash）可以让你无需重启即可在运行时切换。

<!-- ZH_RESOURCES -->
- [The Twelve-Factor App — Config](https://12factor.net/config) -- 类型：指南，时间：10m
- [python-dotenv 文档](https://saurabh-kumar.com/python-dotenv/) -- 类型：工具，时间：10m

<!-- ZH_UI -->
1. 将硬编码值（数据库 URL、API 密钥）从源代码移到环境变量中
2. 理解 12-factor app 的配置方法
3. 本地开发使用 .env 文件，但不要提交到 git
4. 解释为什么配置应随环境变化，而代码不应变化
5. 现在配置已与代码分离。但如何让它在真实服务器上运行，而不只是在我的笔记本电脑上？
6. 我的应用从环境变量读取配置，密钥已从源代码中移出，我可以在不修改任何代码的情况下在开发和生产设置之间切换。但它仍然运行在 localhost 上。我究竟该如何部署这个东西？
