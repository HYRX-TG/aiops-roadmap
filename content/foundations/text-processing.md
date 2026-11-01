---
id: text-processing
title: Text Processing Tools
zone: foundations
edges:
  to:
    - id: scripting-bash-python
      question: I keep writing the same processing pipelines over and over. How do I turn this into a proper script?
      detail: >-
        I've been building these one-liners in my head and running them
        interactively, but now I want to save them, add logic, reuse them.
        What's the right way to take what I know about shell commands and turn
        it into something I can actually automate?
difficulty: 2
tags:
  - awk
  - sed
  - cut
  - sort
  - uniq
  - text-processing
  - shell
  - cli
category: practice
milestones:
  - Extract specific fields from structured text output using cut and awk
  - Count and rank occurrences using sort and uniq -c
  - Use sed for in-place substitution across config files
title_zh: "文本处理工具"

---


grep finds lines. But sometimes you do not want the whole line — you want the third column, or you want to count how many times each value appears, or you want to replace a value across a file. That is where text processing tools come in. `awk`, `sed`, `cut`, `sort`, and `uniq` are the five you reach for constantly. Together with grep and pipes, they let you ask almost any question about text data without writing a single line of Python.

<!-- DEEP_DIVE -->

## cut — extract columns

`cut` splits each line on a delimiter and prints specific fields. It is the fastest way to pull a column out of structured output.

```bash
# Print the first field from /etc/passwd (usernames), split on :
cut -d: -f1 /etc/passwd

# Print fields 1 and 3
cut -d: -f1,3 /etc/passwd

# Print the 9th space-separated field from nginx access logs (status code)
cut -d' ' -f9 /var/log/nginx/access.log
```

`cut` is simple and fast. Its limitation: it only works with a single, consistent delimiter. For anything more complex, use `awk`.

## sort — order output

`sort` reorders lines alphabetically by default. With flags, it gets much more useful:

- `sort -n` — numeric sort. Without this, `10` sorts before `9` (lexicographic).
- `sort -r` — reverse order (descending).
- `sort -rn` — numeric, descending. This is the combination you want for "largest first."
- `sort -k2` — sort by the second field.
- `sort -u` — sort and remove duplicates (like `sort | uniq`).
- `sort -h` — human-readable numeric sort. Handles `1K`, `5M`, `2G` correctly.

```bash
# Largest directories first (the combination you use constantly)
du -sh /var/log/* | sort -rh

# Sort a log file by the numeric value in field 2
awk '{print $2, $0}' app.log | sort -n | cut -d' ' -f2-
```

## uniq — deduplicate and count

`uniq` removes consecutive duplicate lines. Always sort first, because `uniq` only collapses adjacent duplicates.

- `uniq` — remove duplicates
- `uniq -c` — prefix each line with its count. This is the one you use constantly.
- `uniq -d` — print only the lines that appear more than once
- `uniq -u` — print only lines that appear exactly once

The pattern `sort | uniq -c | sort -rn` is one of the most useful things you can type in a terminal:

```bash
# What HTTP status codes are my users getting, and how often?
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn

# Which IPs are making the most requests?
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20

# Which error messages appear most often?
grep "ERROR" /var/log/myapp/app.log | sort | uniq -c | sort -rn | head -10
```

## awk — field processing and more

`awk` is a small programming language built around processing text line by line. It is overkill for simple field extraction, but invaluable when you need logic.

The basics: `awk '{print $1}'` prints the first field of each line. Fields are whitespace-separated by default. `$0` is the whole line.

```bash
# Print the 1st and 9th fields from nginx access log (IP and status code)
awk '{print $1, $9}' /var/log/nginx/access.log

# Custom delimiter with -F
awk -F: '{print $1}' /etc/passwd     # first field, colon-delimited

# Conditional: only print lines where field 9 starts with 5 (5xx errors)
awk '$9 ~ /^5/' /var/log/nginx/access.log

# Sum a column (total bytes transferred)
awk '{sum += $10} END {print sum}' /var/log/nginx/access.log

# Print lines where the value in column 2 is greater than 1000
awk '$2 > 1000' metrics.log
```

awk's `BEGIN` and `END` blocks run before and after processing all lines, which is how you do aggregations like sums and counts.

## sed — stream editing

`sed` edits text as it flows through a pipe, or edits files in place. Its most common use is substitution:

```bash
# Replace "localhost" with "db.internal" in a config file (prints to stdout)
sed 's/localhost/db.internal/' config.yaml

# In-place edit (modify the file directly). Use -i.bak to keep a backup.
sed -i.bak 's/localhost/db.internal/g' config.yaml

# The g flag at the end replaces ALL occurrences on each line, not just the first.
sed 's/foo/bar/g' file.txt

# Delete lines matching a pattern
sed '/^#/d' config.conf     # remove comment lines
sed '/^$/d' config.conf     # remove blank lines

# Print only lines 10 through 20
sed -n '10,20p' bigfile.log
```

`sed` is most useful for quick substitutions across files. For more complex transformations, a Python script is often clearer.

## Putting it together

These tools compose. The real skill is knowing which to reach for and in what order:

```bash
# How many unique users hit my API in the last hour?
tail -n 10000 /var/log/nginx/access.log | awk '{print $1}' | sort -u | wc -l

# Top 10 slowest request URIs by average response time
awk '{print $7, $NF}' /var/log/nginx/access.log | \
  awk '{sum[$1]+=$2; count[$1]++} END {for(u in sum) print sum[u]/count[u], u}' | \
  sort -rn | head -10

# Find all environment variables set in config files that look like secrets
grep -r "password\|secret\|token\|key" /etc/ 2>/dev/null | \
  grep -v "^Binary" | cut -d: -f1 | sort -u
```

You will not memorize all of this immediately. The pattern to build is: know what each tool does, know when to reach for it, and know how to look up the flags when you need them.

<!-- RESOURCES -->

- [AWK Tutorial - grymoire.com](https://www.grymoire.com/Unix/Awk.html) -- type: tutorial, time: 1h
- [sed Tutorial - grymoire.com](https://www.grymoire.com/Unix/Sed.html) -- type: tutorial, time: 1h
- [The Art of Command Line (GitHub)](https://github.com/jlevy/the-art-of-command-line) -- type: reference, time: varies
- [Command-line Tools can be 235x Faster than your Hadoop Cluster](https://adamdrake.com/command-line-tools-can-be-235x-faster-than-your-hadoop-cluster.html) -- type: article, time: 10m

<!-- ZH_SUMMARY -->
grep 查找的是整行内容。但有时你并不需要整行——你想要的是第三列，或者想统计每个值出现了多少次，又或者想在整个文件中替换某个值。这正是文本处理工具的用武之地。`awk`、`sed`、`cut`、`sort` 和 `uniq` 是你经常要用到的五个工具。将它们与 grep 和管道结合起来，你几乎可以对文本数据提出任何问题，而无需编写一行 Python 代码。

<!-- ZH_DEEP_DIVE -->
## cut — 提取列

`cut` 按分隔符拆分每一行并打印指定字段。它是从结构化输出中提取某一列最快的方式。

```bash
# 打印 /etc/passwd 的第一个字段（用户名），以 : 分隔
cut -d: -f1 /etc/passwd

# 打印第 1 和第 3 个字段
cut -d: -f1,3 /etc/passwd

# 打印 nginx 访问日志中以空格分隔的第 9 个字段（状态码）
cut -d' ' -f9 /var/log/nginx/access.log
```

`cut` 简单且快速。它的局限在于：只能处理单一且一致的分隔符。遇到更复杂的情况，请使用 `awk`。

## sort — 排序输出

`sort` 默认按字母顺序重排行。加上参数后，它会变得有用得多：

- `sort -n` — 按数值排序。不加此参数时，`10` 会排在 `9` 前面（字典序）。
- `sort -r` — 逆序（降序）。
- `sort -rn` — 按数值降序。这就是“最大值在前”时你想要的组合。
- `sort -k2` — 按第二个字段排序。
- `sort -u` — 排序并去重（类似 `sort | uniq`）。
- `sort -h` — 人类可读的数值排序。能正确处理 `1K`、`5M`、`2G`。

```bash
# 最大的目录排在前面（你会经常用到的组合）
du -sh /var/log/* | sort -rh

# 按第 2 个字段的数值对日志文件排序
awk '{print $2, $0}' app.log | sort -n | cut -d' ' -f2-
```

## uniq — 去重与计数

`uniq` 移除连续的重复行。务必先排序，因为 `uniq` 只会合并相邻的重复行。

- `uniq` — 移除重复行
- `uniq -c` — 在每行前加上出现次数。这是你会经常用到的那个。
- `uniq -d` — 只打印出现不止一次的行
- `uniq -u` — 只打印恰好出现一次的行

`sort | uniq -c | sort -rn` 是你在终端里能敲出的最有用的命令之一：

```bash
# 我的用户正在收到哪些 HTTP 状态码，频率如何？
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn

# 哪些 IP 发出的请求最多？
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20

# 哪些错误消息出现得最频繁？
grep "ERROR" /var/log/myapp/app.log | sort | uniq -c | sort -rn | head -10
```

## awk — 字段处理及更多

`awk` 是一门围绕逐行处理文本构建的小型编程语言。对于简单的字段提取来说它有些大材小用，但当你需要逻辑处理时，它价值无穷。

基础用法：`awk '{print $1}'` 打印每一行的第一个字段。字段默认以空白分隔。`$0` 表示整行。

```bash
# 打印 nginx 访问日志的第 1 和第 9 个字段（IP 和状态码）
awk '{print $1, $9}' /var/log/nginx/access.log

# 用 -F 指定自定义分隔符
awk -F: '{print $1}' /etc/passwd     # 第一个字段，以冒号分隔

# 条件判断：只打印第 9 个字段以 5 开头的行（5xx 错误）
awk '$9 ~ /^5/' /var/log/nginx/access.log

# 对某一列求和（传输的总字节数）
awk '{sum += $10} END {print sum}' /var/log/nginx/access.log

# 打印第 2 列的值大于 1000 的行
awk '$2 > 1000' metrics.log
```

awk 的 `BEGIN` 和 `END` 块分别在处理所有行之前和之后运行，这就是你实现求和、计数等聚合操作的方式。

## sed — 流编辑

`sed` 在文本流经管道时进行编辑，或就地编辑文件。它最常见的用途是替换：

```bash
# 在配置文件中把 "localhost" 替换为 "db.internal"（输出到 stdout）
sed 's/localhost/db.internal/' config.yaml

# 就地编辑（直接修改文件）。使用 -i.bak 保留备份。
sed -i.bak 's/localhost/db.internal/g' config.yaml

# 末尾的 g 标志会替换每行中所有出现的位置，而不仅仅是第一个。
sed 's/foo/bar/g' file.txt

# 删除匹配某个模式的行
sed '/^#/d' config.conf     # 移除注释行
sed '/^$/d' config.conf     # 移除空行

# 只打印第 10 到第 20 行
sed -n '10,20p' bigfile.log
```

`sed` 最适合用于跨文件的快速替换。对于更复杂的转换，Python 脚本通常更清晰。

## 组合使用

这些工具可以组合。真正的技能在于知道该用哪个、以及以什么顺序使用：

```bash
# 过去一小时内有多少唯一用户访问了我的 API？
tail -n 10000 /var/log/nginx/access.log | awk '{print $1}' | sort -u | wc -l

# 按平均响应时间排名的前 10 个最慢请求 URI
awk '{print $7, $NF}' /var/log/nginx/access.log | \
  awk '{sum[$1]+=$2; count[$1]++} END {for(u in sum) print sum[u]/count[u], u}' | \
  sort -rn | head -10

# 查找配置文件中所有看起来像密钥的环境变量
grep -r "password\|secret\|token\|key" /etc/ 2>/dev/null | \
  grep -v "^Binary" | cut -d: -f1 | sort -u
```

你不会立刻记住所有这些。要建立的模式是：知道每个工具做什么，知道何时该用它，并知道在需要时如何查阅参数。

<!-- ZH_RESOURCES -->
- [AWK 教程 - grymoire.com](https://www.grymoire.com/Unix/Awk.html) -- 类型: 教程, 时长: 1小时
- [sed 教程 - grymoire.com](https://www.grymoire.com/Unix/Sed.html) -- 类型: 教程, 时长: 1小时
- [命令行艺术 (GitHub)](https://github.com/jlevy/the-art-of-command-line) -- 类型: 参考, 时长: 不定
- [命令行工具可以比你的 Hadoop 集群快 235 倍](https://adamdrake.com/command-line-tools-can-be-235x-faster-than-your-hadoop-cluster.html) -- 类型: 文章, 时长: 10分钟

<!-- ZH_UI -->
1. 使用 cut 和 awk 从结构化文本输出中提取特定字段
2. 使用 sort 和 uniq -c 统计并排序出现次数
3. 使用 sed 对配置文件进行就地替换
4. 我一直在反复编写相同的处理管道。如何把它变成一个正式的脚本？
5. 我一直在脑子里构建这些单行命令并交互式运行，但现在我想保存它们、添加逻辑、复用它们。把我所掌握的 shell 命令知识变成真正可以自动化的东西，正确的方式是什么？
