---
id: regular-expressions
title: Regular Expressions
zone: foundations
edges:
  to:
    - id: text-processing
      question: I can match patterns — now how do I use them to transform text, not just find it?
      detail: >-
        grep with regex is great for finding things, but I want to do more —
        extract a field from each line, replace a value across a file, strip
        out parts I don't care about. The pattern knowledge I have now should
        work for that, right? What are the tools that let me actually modify
        and reshape text?
difficulty: 2
tags:
  - regex
  - regular-expressions
  - grep
  - pattern-matching
  - shell
category: concept
milestones:
  - Write a regex that matches IP addresses, timestamps, and HTTP status codes
  - Use character classes, anchors, and quantifiers correctly
  - Explain the difference between basic and extended regex
title_zh: "正则表达式"

---


You have been writing patterns in grep and they mostly work, but it feels like guessing. Regular expressions are the formal language behind those patterns — a compact syntax for describing what text looks like. Once you understand the rules, you can write patterns confidently instead of copying them from Stack Overflow and hoping for the best. In SRE work, regex comes up constantly: searching logs, writing alerts, parsing output, validating config.

<!-- DEEP_DIVE -->

## The building blocks

A regular expression is a pattern that describes a set of strings. At its simplest, a literal string like `error` matches any line containing the word "error". The power comes from special characters that match *classes* of text.

**The dot `.`** matches any single character. `er.or` matches "error", "er_or", "er3or" — anything with two characters between `er` and `or`.

**Quantifiers** — how many times something repeats:

- `*` — zero or more. `er.*or` matches "error", "eror", "erXXXXor", even "eror" with nothing in between.
- `+` — one or more. `er.+or` requires at least one character between them.
- `?` — zero or one. `https?://` matches both "http://" and "https://".
- `{3}` — exactly 3. `[0-9]{3}` matches exactly three digits.
- `{2,4}` — between 2 and 4.

**Character classes `[]`** — match one character from a set:

- `[0-9]` — any digit
- `[a-z]` — any lowercase letter
- `[A-Za-z]` — any letter
- `[A-Za-z0-9]` — any alphanumeric character
- `[^0-9]` — any character that is **not** a digit (the `^` inside brackets means "not")

**Shorthand character classes** (with `grep -P` or in most regex engines):

- `\d` — digit (same as `[0-9]`)
- `\w` — word character (letter, digit, or underscore)
- `\s` — whitespace (space, tab, newline)

**Anchors** — position, not characters:

- `^` — start of line. `^ERROR` only matches lines that **begin** with ERROR.
- `$` — end of line. `\.log$` matches lines ending with `.log`.

**Alternation `|`** — this or that. `ERROR|WARN|FATAL` matches any of the three. Requires `grep -E` (extended regex).

**Grouping `()`** — group parts of a pattern. `(ERROR|WARN): ` matches either word followed by a colon and space. Also used for capturing in tools like sed and awk.

**Escaping `\`** — to match a literal special character, escape it. `\.` matches a literal dot (not any character). `\(` matches a literal parenthesis.

## grep -E vs grep -P

By default `grep` uses basic regex, where `+`, `?`, `|`, `()`, and `{}` need to be escaped with `\` to have special meaning — backwards from what you'd expect. Use `grep -E` (extended regex) to avoid this. Most people use `-E` by default.

`grep -P` enables Perl-compatible regex (PCRE), which adds `\d`, `\w`, `\s`, lookaheads, and other features. Not available on all systems (macOS `grep` doesn't support it; use `ggrep` from Homebrew).

## Practical patterns for SRE

```bash
# Match an IPv4 address
grep -E "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"

# Match HTTP 5xx status codes in nginx logs
grep -E '" 5[0-9]{2} '

# Match lines with a timestamp in [2024-01-15 10:23:45] format
grep -E "\[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\]"

# Find lines that start with ERROR or FATAL
grep -E "^(ERROR|FATAL)"

# Find log lines that do NOT contain "healthcheck"
grep -v "healthcheck"

# Find config lines that aren't comments or empty
grep -E "^[^#]" /etc/myapp/config.conf | grep -v "^$"
```

## Common mistakes

**Matching too much.** `.*` is greedy — it matches as much as possible. `error.*timeout` can match a huge chunk of a line. Be more specific when you can.

**Forgetting anchors.** `error` matches anywhere in the line, including "no-error" and "erroring". Use `^error` if you only want lines starting with it, or `\berror\b` (word boundary) if you want the whole word.

**Special characters in data.** IP addresses contain dots, log paths contain slashes, URLs contain question marks. If you are matching literal text, escape the special characters: `192\.168\.1\.1` not `192.168.1.1` (which would match "192X168Y1Z1" too).

**Case sensitivity.** grep is case-sensitive by default. Use `-i` when case doesn't matter.

## Building patterns incrementally

Do not try to write a complex regex in one go. Start simple and refine:

```bash
# Start: find lines with "payment"
grep "payment" /var/log/myapp/app.log

# Refine: only failed payments
grep "payment.*failed" /var/log/myapp/app.log

# Refine more: only lines where it's a specific error code
grep -E "payment.*failed.*code=[0-9]+" /var/log/myapp/app.log

# Check your count
grep -cE "payment.*failed.*code=[0-9]+" /var/log/myapp/app.log
```

Test each step. Regex is much easier to write and debug incrementally than all at once.

<!-- RESOURCES -->

- [Regexr - Interactive regex tester with explanation](https://regexr.com/) -- type: tool, time: 30m
- [Regular-Expressions.info - Comprehensive reference](https://www.regular-expressions.info/) -- type: reference, time: varies
- [RegexOne - Learn by doing](https://regexone.com/) -- type: tutorial, time: 1h
- [grep manual - regex section](https://www.gnu.org/software/grep/manual/grep.html#Regular-Expressions) -- type: reference, time: 20m

<!-- ZH_SUMMARY -->
你一直在用 grep 编写模式，它们大多能正常工作，但感觉像是在猜。正则表达式是这些模式背后的形式语言——一种用于描述文本形态的紧凑语法。一旦理解了规则，你就能自信地编写模式，而不必从 Stack Overflow 上复制粘贴、然后祈祷它能用。在 SRE 工作中，正则表达式无处不在：搜索日志、编写告警、解析输出、校验配置。

<!-- ZH_DEEP_DIVE -->
## 构建模块

正则表达式是一种描述一组字符串的模式。最简单的形式是像 `error` 这样的字面字符串，它匹配任何包含单词 "error" 的行。其强大之处在于那些匹配文本*类别*的特殊字符。

**点号 `.`** 匹配任意单个字符。`er.or` 匹配 "error"、"er_or"、"er3or"——即 `er` 和 `or` 之间有两个任意字符的任何内容。

**量词**——表示某内容重复的次数：

- `*`——零次或多次。`er.*or` 匹配 "error"、"eror"、"erXXXXor"，甚至中间没有任何字符的 "eror"。
- `+`——一次或多次。`er.+or` 要求两者之间至少有一个字符。
- `?`——零次或一次。`https?://` 同时匹配 "http://" 和 "https://"。
- `{3}`——恰好 3 次。`[0-9]{3}` 恰好匹配三位数字。
- `{2,4}`——2 到 4 次之间。

**字符类 `[]`**——从集合中匹配一个字符：

- `[0-9]`——任意数字
- `[a-z]`——任意小写字母
- `[A-Za-z]`——任意字母
- `[A-Za-z0-9]`——任意字母数字字符
- `[^0-9]`——任意**不是**数字的字符（方括号内的 `^` 表示"非"）

**简写字符类**（配合 `grep -P` 或在大多数正则引擎中）：

- `\d`——数字（等同于 `[0-9]`）
- `\w`——单词字符（字母、数字或下划线）
- `\s`——空白字符（空格、制表符、换行符）

**锚点**——表示位置，而非字符：

- `^`——行首。`^ERROR` 只匹配以 ERROR **开头**的行。
- `$`——行尾。`\.log$` 匹配以 `.log` 结尾的行。

**交替 `|`**——这个或那个。`ERROR|WARN|FATAL` 匹配三者中的任意一个。需要 `grep -E`（扩展正则）。

**分组 `()`**——将模式的各部分分组。`(ERROR|WARN): ` 匹配后跟冒号和空格的任一单词。也用于 sed 和 awk 等工具中的捕获。

**转义 `\`**——要匹配字面的特殊字符，需对其进行转义。`\.` 匹配字面点号（而非任意字符）。`\(` 匹配字面括号。

## grep -E 与 grep -P

默认情况下 `grep` 使用基本正则，其中 `+`、`?`、`|`、`()` 和 `{}` 需要加 `\` 转义才具有特殊含义——这与你预期的正好相反。使用 `grep -E`（扩展正则）可以避免这一点。大多数人默认使用 `-E`。

`grep -P` 启用 Perl 兼容正则（PCRE），它增加了 `\d`、`\w`、`\s`、先行断言及其他特性。并非所有系统都支持（macOS 的 `grep` 不支持；请使用 Homebrew 提供的 `ggrep`）。

## SRE 实用模式

```bash
# Match an IPv4 address
grep -E "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"

# Match HTTP 5xx status codes in nginx logs
grep -E '" 5[0-9]{2} '

# Match lines with a timestamp in [2024-01-15 10:23:45] format
grep -E "\[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\]"

# Find lines that start with ERROR or FATAL
grep -E "^(ERROR|FATAL)"

# Find log lines that do NOT contain "healthcheck"
grep -v "healthcheck"

# Find config lines that aren't comments or empty
grep -E "^[^#]" /etc/myapp/config.conf | grep -v "^$"
```

## 常见错误

**匹配过多。** `.*` 是贪婪的——它会尽可能多地匹配。`error.*timeout` 可能匹配一行中一大段内容。在可能的情况下应更精确。

**忘记锚点。** `error` 会匹配行中任意位置，包括 "no-error" 和 "erroring"。如果只想匹配以它开头的行，请使用 `^error`；如果想匹配整个单词，请使用 `\berror\b`（单词边界）。

**数据中的特殊字符。** IP 地址包含点号，日志路径包含斜杠，URL 包含问号。如果要匹配字面文本，请转义特殊字符：使用 `192\.168\.1\.1` 而非 `192.168.1.1`（后者也会匹配 "192X168Y1Z1"）。

**大小写敏感。** grep 默认区分大小写。当大小写无关紧要时使用 `-i`。

## 逐步构建模式

不要试图一次性写出复杂的正则。从简单开始，逐步细化：

```bash
# Start: find lines with "payment"
grep "payment" /var/log/myapp/app.log

# Refine: only failed payments
grep "payment.*failed" /var/log/myapp/app.log

# Refine more: only lines where it's a specific error code
grep -E "payment.*failed.*code=[0-9]+" /var/log/myapp/app.log

# Check your count
grep -cE "payment.*failed.*code=[0-9]+" /var/log/myapp/app.log
```

逐步测试每一步。逐步编写和调试正则要比一次性完成容易得多。

<!-- ZH_RESOURCES -->
- [Regexr - 交互式正则表达式测试器，附带解释](https://regexr.com/) -- 类型：工具，时间：30分钟
- [Regular-Expressions.info - 全面参考](https://www.regular-expressions.info/) -- 类型：参考，时间：不定
- [RegexOne - 边做边学](https://regexone.com/) -- 类型：教程，时间：1小时
- [grep 手册 - 正则表达式部分](https://www.gnu.org/software/grep/manual/grep.html#Regular-Expressions) -- 类型：参考，时间：20分钟

<!-- ZH_UI -->
1. 编写一个正则表达式，匹配 IP 地址、时间戳和 HTTP 状态码
2. 正确使用字符类、锚点和量词
3. 解释基本正则与扩展正则的区别
4. 我能匹配模式了——现在如何用它们来转换文本，而不只是查找？
5. 用正则配合 grep 查找很方便，但我想做更多——从每行提取字段、在整个文件中替换某个值、去掉我不关心的部分。我现在掌握的模式知识应该能派上用场，对吧？有哪些工具能让我真正修改和重塑文本？
