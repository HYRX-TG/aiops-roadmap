---
id: static-site
title: Building a Static Website
zone: building
edges:
  to:
    - id: dynamic-web-app
      question: >-
        My site looks nice, but it can't actually do anything. How do I add real
        functionality?
      detail: >-
        My static site looks great but it's basically a fancy brochure. I want
        users to be able to log in, submit forms, see personalized content —
        things that require actually remembering something. I have no idea how
        to make a webpage do that.
difficulty: 1
tags:
  - html
  - css
  - javascript
  - static-site
  - web-basics
category: concept
milestones:
  - Build a static HTML page with CSS styling
  - Add JavaScript interactivity to the page
  - 'Deploy it somewhere basic (GitHub Pages, Netlify)'
title_zh: "构建静态网站"

---


You know how to write scripts that automate tasks. Now you want to build something people can actually see and use — a website. Maybe you have an idea for an online store, a portfolio, or a tool. It all starts the same way: HTML for structure, CSS for styling, and JavaScript for interactivity. This is the foundation of everything on the web.

<!-- DEEP_DIVE -->

A **static website** is a collection of files — HTML, CSS, JavaScript, images — that a browser downloads and renders directly. There is no server-side logic, no database, no processing. The server just hands over files, and the browser does all the work. This is how the web started, and it is still how a huge portion of the internet works today.

**HTML** (HyperText Markup Language) is the skeleton. It defines what is on the page — headings, paragraphs, images, links, forms. Here is the simplest possible webpage:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Online Store</title>
</head>
<body>
    <h1>Welcome to My Store</h1>
    <p>We sell the finest widgets.</p>
    <ul>
        <li>Widget A - $10</li>
        <li>Widget B - $20</li>
        <li>Widget C - $30</li>
    </ul>
</body>
</html>
```

Save that as `index.html`, open it in a browser, and you have a website. It is ugly, but it works.

**CSS** (Cascading Style Sheets) makes it look good. Colors, fonts, layout, spacing — all CSS. You can add it inline, in a `<style>` tag, or in a separate `.css` file. Modern CSS is incredibly powerful — you can build responsive layouts that work on phones and desktops, add animations, and create professional-looking designs without any JavaScript.

**JavaScript** adds behavior. Want a button that does something when clicked? A form that validates input? A product filter? That is JavaScript. It runs in the browser and can manipulate the HTML and CSS dynamically.

For an online store idea, you can get surprisingly far with just static files. You can list products, show images, even build a nice shopping cart UI with JavaScript. But here is the catch — none of it is real. There is no backend to process orders, no database to store users, no way to handle payments. The cart exists only in the browser, and refreshing the page might lose everything. The store looks functional, but it is a facade.

This is the exact moment most developers hit their first real architectural decision: the static site looks great, but it cannot actually do the thing it needs to do. You need a backend. You need a database. You need a dynamic web application.

**Deploying a static site** is almost trivially easy. GitHub Pages lets you push HTML files to a repository and they are live on the internet. Netlify and Vercel do the same with drag-and-drop. This is worth doing early — seeing your creation live on a real URL is motivating, and it teaches you the deployment cycle that you will use for the rest of your career.

<!-- RESOURCES -->

- [MDN Web Docs - HTML Basics](https://developer.mozilla.org/en-US/docs/Learn/Getting_started_with_the_web/HTML_basics) -- type: tutorial, time: 1h
- [MDN Web Docs - CSS First Steps](https://developer.mozilla.org/en-US/docs/Learn/CSS/First_steps) -- type: tutorial, time: 2h
- [JavaScript.info - The Modern JavaScript Tutorial](https://javascript.info/) -- type: tutorial, time: varies
- [GitHub Pages Documentation](https://pages.github.com/) -- type: tool, time: 15m

<!-- ZH_SUMMARY -->
你已掌握编写自动化任务脚本的能力。现在你想构建人们真正能看到并使用的东西——一个网站。也许你有一个在线商店、作品集或工具的想法。一切的开端都是相同的：用 HTML 构建结构，用 CSS 进行样式设计，用 JavaScript 实现交互。这是 Web 上一切事物的基础。

<!-- ZH_DEEP_DIVE -->
**静态网站**是一组文件——HTML、CSS、JavaScript、图片——由浏览器直接下载并渲染。没有服务端逻辑，没有数据库，没有处理过程。服务器只是把文件交给浏览器，所有工作都由浏览器完成。这就是 Web 的起点，如今互联网的很大一部分仍然是这样运作的。

**HTML**（超文本标记语言）是骨架。它定义了页面上有什么——标题、段落、图片、链接、表单。下面是最简单的网页：

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Online Store</title>
</head>
<body>
    <h1>Welcome to My Store</h1>
    <p>We sell the finest widgets.</p>
    <ul>
        <li>Widget A - $10</li>
        <li>Widget B - $20</li>
        <li>Widget C - $30</li>
    </ul>
</body>
</html>
```

把它保存为 `index.html`，在浏览器中打开，你就有了一个网站。它很丑，但能用。

**CSS**（层叠样式表）让它变得好看。颜色、字体、布局、间距——全都靠 CSS。你可以内联添加，放在 `<style>` 标签里，或者放在单独的 `.css` 文件中。现代 CSS 极其强大——你可以构建在手机和桌面上都能正常工作的响应式布局，添加动画，并在完全不使用 JavaScript 的情况下做出专业水准的设计。

**JavaScript** 添加行为。想要一个点击后执行某些操作的按钮？一个校验输入的表单？一个商品筛选器？那就是 JavaScript。它在浏览器中运行，可以动态操作 HTML 和 CSS。

对于在线商店这个想法，仅靠静态文件你就能走得惊人地远。你可以列出商品、展示图片，甚至用 JavaScript 构建一个漂亮的购物车 UI。但问题在于——这些都不是真的。没有后端来处理订单，没有数据库来存储用户，没有办法处理支付。购物车只存在于浏览器中，刷新页面可能就会丢失一切。商店看起来功能齐全，但它只是一个空壳。

这正是大多数开发者遇到第一个真正架构决策的时刻：静态网站看起来很棒，但它实际上无法完成它需要完成的事情。你需要一个后端。你需要一个数据库。你需要一个动态 Web 应用。

**部署静态网站**几乎轻而易举。GitHub Pages 让你把 HTML 文件推送到一个仓库，它们就能上线到互联网。Netlify 和 Vercel 通过拖放也能做到同样的事。这值得尽早做——看到自己的作品上线在一个真实的 URL 上很有激励作用，而且它会教你部署循环，你将在余下的职业生涯中一直使用它。

<!-- ZH_RESOURCES -->
- [MDN Web Docs - HTML 基础](https://developer.mozilla.org/en-US/docs/Learn/Getting_started_with_the_web/HTML_basics) -- 类型：教程，时长：1小时
- [MDN Web Docs - CSS 入门](https://developer.mozilla.org/en-US/docs/Learn/CSS/First_steps) -- 类型：教程，时长：2小时
- [JavaScript.info - 现代 JavaScript 教程](https://javascript.info/) -- 类型：教程，时长：不定
- [GitHub Pages 文档](https://pages.github.com/) -- 类型：工具，时长：15分钟

<!-- ZH_UI -->
1. 构建一个带 CSS 样式的静态 HTML 页面
2. 为页面添加 JavaScript 交互
3. 将其部署到基础平台（GitHub Pages、Netlify）
4. 我的网站看起来不错，但实际什么都做不了。如何添加真正的功能？
5. 我的静态网站看起来很棒，但基本就是个花哨的宣传册。我希望用户能够登录、提交表单、查看个性化内容——这些都需要真正记住一些东西。我完全不知道如何让网页做到这一点。
