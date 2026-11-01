---
id: dynamic-web-app
title: Dynamic Web Applications
zone: building
edges:
  to:
    - id: it-works-on-my-laptop
      question: My app works locally. How do I let other people use it?
      detail: >-
        My app works perfectly on localhost — but when I try to show it to
        someone, I have nothing to send them. It's not on the internet, it's
        just on my laptop. How do I get it somewhere real people can actually
        reach it?
    - id: databases-and-sql
      question: >-
        Where does my data actually live? Variables disappear when the app
        restarts.
      detail: >-
        I restart my app and everything disappears — all the data I added is
        gone. Variables don't survive a restart, and that means I can't actually
        build anything real without somewhere to actually store stuff. What does
        it take to make my app remember things?
    - id: apis-and-rest
      question: >-
        My frontend and backend are tangled together. How do different parts of
        a system talk to each other?
      detail: >-
        My backend generates HTML and my frontend is completely tangled into it.
        But I want a mobile app too, or maybe to let someone else integrate with
        my service. The backend can't keep generating HTML for everything —
        there must be a cleaner way to expose what my app does.
    - id: authentication-basics
      question: >-
        Anyone can access everything in my app right now. How do I make it
        so only the right people can see the right things?
      detail: >-
        There's no login, no accounts, nothing. Anyone who visits the URL
        sees everything. I need users to sign up, log in, and only see their
        own data. But I don't even know how login actually works under the
        hood — cookies? Tokens? Sessions?
    - id: app-configuration
      question: >-
        I have database passwords and API keys hardcoded in my source code.
        That can't be right.
      detail: >-
        My database URL says localhost, my API key is on line 42, and if I
        ever push this to GitHub the whole world can see my credentials.
        Plus, none of this will work on a real server because everything is
        hardcoded for my laptop. How do I separate config from code?
    - id: testing-basics
      question: How do I know my code actually works before I ship it?
      detail: >-
        I test by running the app, clicking around, and hoping nothing broke.
        That was fine when it was small, but now I'm scared to touch things — I
        have no idea if changing one part will quietly break something else. How
        do I get confidence that my code still works after I change it?
    - id: version-control-git
      question: I keep overwriting my own code. How do I track changes?
      detail: >-
        I've already overwritten code I needed to keep. I have no way to undo
        mistakes, no record of what changed, and no idea how I'd work on this
        with someone else without everything turning into chaos. There must be a
        way to track all of this.
difficulty: 1
tags:
  - flask
  - django
  - backend
  - database
  - web-app
  - python
category: concept
milestones:
  - Run a Flask or Django app locally
  - Connect the app to a database (SQLite or PostgreSQL)
  - 'Build a feature that reads and writes data (e.g., user registration)'
title_zh: "动态 Web 应用"

---


Your static site looks great, but it cannot do anything real. It cannot remember who visited, cannot process a purchase, cannot store data. To build a real application — one that handles users, orders, and dynamic content — you need a backend: server-side code that runs on a machine, processes requests, and talks to a database.

<!-- DEEP_DIVE -->

A **dynamic web application** has two parts: a frontend (what users see in their browser) and a backend (server-side code that handles logic and data). When a user clicks "Add to Cart," the browser sends a request to your backend, which validates the item, updates the database, and sends back a response. This request-response cycle is the heartbeat of every web application.

**Flask** is the perfect starting point for Python developers. It is minimal, explicit, and teaches you exactly what is happening:

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

products = [
    {"id": 1, "name": "Widget A", "price": 10},
    {"id": 2, "name": "Widget B", "price": 20},
]

@app.route("/products")
def list_products():
    return jsonify(products)

@app.route("/order", methods=["POST"])
def place_order():
    data = request.json
    # In a real app, this would save to a database
    return jsonify({"status": "order placed", "item": data["product_id"]})

if __name__ == "__main__":
    app.run(debug=True)
```

Run `python app.py` and you have a web server listening on `http://localhost:5000`. Visit `/products` in your browser and you get JSON back. Send a POST to `/order` and it processes it. This is a real web service.

**Databases** are where your data lives permanently. SQLite is built into Python and perfect for learning — no setup required. For production, PostgreSQL is the standard. The key concepts are tables (structured data), queries (reading data), and transactions (writing data safely). An ORM like SQLAlchemy lets you work with databases using Python objects instead of writing raw SQL:

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_name = db.Column(db.String(120), nullable=False)
    total = db.Column(db.Float, nullable=False)
```

Now your store can actually remember things. Users can sign up, browse products, add items to a cart that persists, and place orders that are saved in a database.

**Django** is the other major Python web framework. Where Flask gives you building blocks and lets you choose your own architecture, Django gives you a complete package — admin panel, ORM, authentication, form handling — all built in. It is opinionated but incredibly productive. Many large-scale applications (Instagram, Pinterest, Disqus) were built with Django.

The pattern you are building here — a **monolith** — is a single application that handles everything: serving pages, processing business logic, managing the database. This is the right architecture when you are starting out. Microservices, APIs, and distributed systems come later. First, build something that works.

At this point, you have a working application. You can run `python app.py`, open your browser, and use your online store. It has products, users, a cart, checkout. Everything works. But there is one problem: it only works on `localhost`. It only works on your laptop. Nobody else in the world can use it. And that is where the next challenge begins.

<!-- RESOURCES -->

- [Flask Quickstart](https://flask.palletsprojects.com/en/stable/quickstart/) -- type: tutorial, time: 30m
- [Django Tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/) -- type: tutorial, time: 4h
- [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/en/stable/tutorial/) -- type: tutorial, time: 2h
- [Full Stack Python - Web Frameworks](https://www.fullstackpython.com/web-frameworks.html) -- type: reference, time: 30m

<!-- ZH_SUMMARY -->
你的静态站点看起来很棒，但它做不了任何实际的事情。它无法记住访客是谁，无法处理购买，无法存储数据。要构建一个真正的应用——一个能处理用户、订单和动态内容的应用——你需要一个后端：在机器上运行的服务器端代码，负责处理请求并与数据库交互。

<!-- ZH_DEEP_DIVE -->
**动态 Web 应用**由两部分组成：前端（用户在浏览器中看到的内容）和后端（处理逻辑与数据的服务端代码）。当用户点击“加入购物车”时，浏览器会向后端发送请求，后端校验商品、更新数据库并返回响应。这个请求-响应循环是每个 Web 应用的心跳。

**Flask** 是 Python 开发者的完美起点。它极简、显式，能让你清楚地看到每一步发生了什么：

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

products = [
    {"id": 1, "name": "Widget A", "price": 10},
    {"id": 2, "name": "Widget B", "price": 20},
]

@app.route("/products")
def list_products():
    return jsonify(products)

@app.route("/order", methods=["POST"])
def place_order():
    data = request.json
    # In a real app, this would save to a database
    return jsonify({"status": "order placed", "item": data["product_id"]})

if __name__ == "__main__":
    app.run(debug=True)
```

运行 `python app.py`，你就拥有了一个监听 `http://localhost:5000` 的 Web 服务器。在浏览器中访问 `/products`，你会得到 JSON 响应。向 `/order` 发送 POST 请求，它就会处理。这是一个真实的 Web 服务。

**数据库**是数据永久存放的地方。SQLite 内置于 Python，非常适合学习——无需任何配置。生产环境中，PostgreSQL 是标准选择。核心概念包括表（结构化数据）、查询（读取数据）和事务（安全地写入数据）。像 SQLAlchemy 这样的 ORM 让你可以用 Python 对象操作数据库，而不必编写原始 SQL：

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_name = db.Column(db.String(120), nullable=False)
    total = db.Column(db.Float, nullable=False)
```

现在你的商店真正能记住东西了。用户可以注册、浏览商品、将商品加入持久化的购物车，并下单保存到数据库中。

**Django** 是另一个主要的 Python Web 框架。Flask 提供构建块，让你自行选择架构；而 Django 提供完整套件——管理后台、ORM、认证、表单处理——全部内置。它虽然带有倾向性，但生产力极高。许多大型应用（Instagram、Pinterest、Disqus）都是用 Django 构建的。

你在这里构建的模式——**单体应用**——是一个处理所有事务的单一应用：提供页面、处理业务逻辑、管理数据库。这是起步阶段的正确架构。微服务、API 和分布式系统是后面的事。先构建出能运行的东西。

至此，你有了一个可用的应用。你可以运行 `python app.py`，打开浏览器，使用你的在线商店。它有商品、用户、购物车、结账。一切都能工作。但有一个问题：它只能在 `localhost` 上运行。它只能在你自己的笔记本电脑上运行。世界上其他任何人都无法使用它。而这正是下一个挑战的起点。

<!-- ZH_RESOURCES -->
- [Flask 快速入门](https://flask.palletsprojects.com/en/stable/quickstart/) -- 类型：教程，时长：30 分钟
- [Django 教程](https://docs.djangoproject.com/en/stable/intro/tutorial01/) -- 类型：教程，时长：4 小时
- [SQLAlchemy 教程](https://docs.sqlalchemy.org/en/stable/tutorial/) -- 类型：教程，时长：2 小时
- [Full Stack Python - Web 框架](https://www.fullstackpython.com/web-frameworks.html) -- 类型：参考，时长：30 分钟

<!-- ZH_UI -->
1. 在本地运行 Flask 或 Django 应用
2. 将应用连接到数据库（SQLite 或 PostgreSQL）
3. 构建一个读写数据的功能（例如用户注册）
4. 我的应用在本地能跑。怎么让别人也能用？
5. 我的应用在 localhost 上运行完美——但想给别人看时，我没什么能发过去的。它不在互联网上，只在我的笔记本里。怎么把它放到真实用户能访问的地方？
6. 我的数据到底存在哪里？应用重启后变量就消失了。
7. 我重启应用后一切都没了——我添加的所有数据都消失了。变量无法在重启后存活，这意味着如果没有真正存储数据的地方，我就做不出任何真实的东西。要让应用记住东西需要什么？
8. 我的前端和后端纠缠在一起。系统的不同部分之间怎么通信？
9. 我的后端生成 HTML，前端完全纠缠在里面。但我还想要一个移动应用，或者让别人集成我的服务。后端不能一直为所有东西生成 HTML——一定有更干净的方式来暴露应用的功能。
10. 现在任何人都能访问我应用里的所有东西。怎么让只有对的人才能看到对的东西？
11. 没有登录、没有账户，什么都没有。任何访问这个 URL 的人都能看到一切。我需要用户注册、登录，并且只能看到自己的数据。但我甚至不知道登录底层是怎么工作的——cookie？token？session？
12. 我的源代码里硬编码了数据库密码和 API 密钥。这肯定不对。
13. 我的数据库 URL 写的是 localhost，API 密钥在第 42 行，一旦推到 GitHub 全世界都能看到我的凭证。而且这些在真实服务器上都跑不了，因为一切都是为我笔记本硬编码的。怎么把配置和代码分开？
14. 我怎么知道代码在发布前真的能工作？
15. 我靠运行应用、到处点点、祈祷没坏来测试。小的时候还行，但现在我不敢碰东西了——我完全不知道改一处会不会悄悄弄坏另一处。怎么才能确信改完代码后它还能工作？
16. 我老是覆盖自己的代码。怎么追踪变更？
17. 我已经覆盖过需要保留的代码了。我没法撤销错误，没有变更记录，也不知道怎么和别人一起做这个而不变成一团乱。一定有办法追踪所有这些。
