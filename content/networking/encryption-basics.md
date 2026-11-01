---
id: encryption-basics
title: 'Encryption: Why and How'
zone: networking
edges:
  to:
    - id: tls-and-certificates
      zone: running
      question: >-
        I understand encryption. How does the web actually use it to secure
        traffic?
      detail: >-
        I understand the building blocks — symmetric keys, asymmetric keys, the
        key exchange problem. But how does any of that play out when my browser
        connects to an HTTPS site for the first time? How does it establish a
        secure channel with a server it's never talked to before?
difficulty: 2
tags:
  - encryption
  - cryptography
  - symmetric
  - asymmetric
  - keys
  - security
category: concept
milestones:
  - Explain the difference between symmetric and asymmetric encryption
  - Understand why HTTPS matters and what plaintext HTTP exposes
  - Describe the key exchange problem and how asymmetric encryption solves it
title_zh: "加密：原因与方法"

---


Run `curl -v http://example.com` and look at what goes over the wire. The entire HTTP request — the URL, the headers, the body with your password — travels across the network as readable text. Anyone sitting between you and the server can read it. Your ISP, the coffee shop WiFi operator, any compromised router along the way. This is not a theoretical risk — it is trivially easy. Encryption makes the data unreadable to everyone except the intended recipient.

<!-- DEEP_DIVE -->

**Encryption** is the process of scrambling data so that only someone with the right key can read it. The original data is called **plaintext**, and the scrambled version is called **ciphertext**. Without the key, the ciphertext looks like random garbage.

There are two fundamental approaches:

**Symmetric encryption** uses the same key to encrypt and decrypt. Think of it like a lockbox with one key — you lock the box, send it to your friend, and they unlock it with an identical key. It is fast and efficient, which makes it perfect for encrypting large amounts of data.

```
Key:        "my-secret-key-123"

Plaintext:  "password=hunter2&card=4111111111111111"
    ↓ encrypt with key
Ciphertext: "a7f3b2e91d... (unreadable garbage)"
    ↓ decrypt with same key
Plaintext:  "password=hunter2&card=4111111111111111"
```

The algorithms you will encounter: **AES** (Advanced Encryption Standard) is the gold standard — it is what your bank uses, what your phone uses for disk encryption, what almost everything uses. AES-256 (256-bit key) is considered unbreakable with current technology.

**The problem with symmetric encryption:** How do you share the key? If you and the server both need the same key, someone has to send it first. But if you send the key over the network in plaintext, anyone watching can grab it — and then your encryption is worthless. You cannot encrypt the key because you do not have a shared key yet. This is the **key exchange problem**, and it stumped cryptographers for decades.

**Asymmetric encryption** (also called public-key cryptography) solves this. Instead of one key, you have a **key pair** — a public key and a private key. They are mathematically linked but you cannot derive one from the other:

- **Public key** — you share this with everyone. Anyone can use it to encrypt data.
- **Private key** — you keep this secret. Only you can decrypt data encrypted with your public key.

```
Server generates a key pair:
  Public key:  (shared openly)
  Private key: (kept secret on server)

Your browser:
  1. Gets the server's public key
  2. Encrypts data with the public key
  3. Sends the ciphertext

The server:
  1. Receives the ciphertext
  2. Decrypts with its private key
  3. Reads the original data

Anyone intercepting the ciphertext cannot decrypt it —
they don't have the private key.
```

The most common asymmetric algorithm is **RSA**. Others include **ECDSA** (Elliptic Curve) and **Ed25519** — you have seen Ed25519 if you have ever generated an SSH key with `ssh-keygen -t ed25519`.

**Asymmetric encryption is slow.** Much slower than symmetric. Encrypting an entire web page with RSA would be painfully slow. So in practice, the web uses **both**:

1. Asymmetric encryption to securely exchange a symmetric key (solving the key exchange problem)
2. Symmetric encryption (AES) for the actual data transfer (fast)

This is exactly what happens when your browser connects to a website over HTTPS. The two sides use asymmetric crypto to agree on a shared symmetric key, and then use that key for the rest of the conversation. You get the security of asymmetric key exchange with the speed of symmetric encryption.

**Hashing** is related but different. A hash function takes input of any size and produces a fixed-size output (a "digest"). It is a one-way function — you cannot reverse a hash to get the original input. Hashing is used for:

- **Password storage** — store the hash, not the password. When a user logs in, hash their input and compare.
- **Data integrity** — hash a file, send the file and the hash. The recipient hashes the file and checks if it matches.
- **Digital signatures** — hash a message, encrypt the hash with a private key. Anyone with the public key can verify the signature.

Common hash functions: **SHA-256** (secure, widely used), **bcrypt/argon2** (designed for passwords, intentionally slow).

```bash
# Hash a string with SHA-256
echo -n "hello world" | sha256sum
# b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9

# Change one character, the hash changes completely
echo -n "hello worle" | sha256sum
# completely different hash
```

**Why SREs care:** Encryption is not optional — it is the foundation of secure communication. Understanding symmetric vs asymmetric, key exchange, and hashing helps you debug TLS issues, manage certificates, configure SSH, handle secrets management, and understand security incidents. Every HTTPS connection, every SSH session, every API call with an auth token relies on these concepts.

<!-- RESOURCES -->

- [Khan Academy - Cryptography](https://www.khanacademy.org/computing/computer-science/cryptography) -- type: interactive, time: 2h
- [Cloudflare - What is encryption?](https://www.cloudflare.com/learning/ssl/what-is-encryption/) -- type: article, time: 10m
- [The Code Book - Simon Singh](https://simonsingh.net/books/the-code-book/) -- type: book, time: varies
- [Practical Cryptography for Developers (free)](https://cryptobook.nakov.com/) -- type: book, time: varies

<!-- ZH_SUMMARY -->
运行 `curl -v http://example.com`，观察网络上传输的内容。整个 HTTP 请求——URL、请求头、包含你密码的请求体——都以可读文本的形式在网络中传输。任何位于你和服务器之间的人都能读取它。你的 ISP、咖啡店 WiFi 运营者、沿途任何被攻陷的路由器。这不是理论上的风险——它极其容易实现。加密使数据对除预期接收者之外的所有人都不可读。

<!-- ZH_DEEP_DIVE -->
**加密**是将数据打乱的过程，只有拥有正确密钥的人才能读取。原始数据称为**明文**，打乱后的版本称为**密文**。没有密钥，密文看起来就像随机的乱码。

有两种基本方法：

**对称加密**使用相同的密钥进行加密和解密。可以把它想象成一个只有一把钥匙的锁箱——你锁上箱子，寄给你的朋友，他们用一把相同的钥匙打开它。它快速且高效，非常适合加密大量数据。

```
Key:        "my-secret-key-123"

Plaintext:  "password=hunter2&card=4111111111111111"
    ↓ encrypt with key
Ciphertext: "a7f3b2e91d... (unreadable garbage)"
    ↓ decrypt with same key
Plaintext:  "password=hunter2&card=4111111111111111"
```

你会遇到的算法：**AES**（高级加密标准）是黄金标准——你的银行在用，你的手机用于磁盘加密，几乎所有东西都在用。AES-256（256 位密钥）被认为在当前技术下无法破解。

**对称加密的问题：** 你如何共享密钥？如果你和服务器都需要相同的密钥，就必须有人先把它发送出去。但如果你以明文形式通过网络发送密钥，任何监听的人都能截获它——然后你的加密就毫无价值了。你无法加密密钥，因为你还没有共享密钥。这就是**密钥交换问题**，它困扰了密码学家数十年。

**非对称加密**（也称为公钥密码学）解决了这个问题。你不是只有一把密钥，而是有一个**密钥对**——一个公钥和一个私钥。它们在数学上相互关联，但你无法从其中一个推导出另一个：

- **公钥**——你与所有人共享。任何人都可以用它来加密数据。
- **私钥**——你将其保密。只有你能解密用你的公钥加密的数据。

```
Server generates a key pair:
  Public key:  (shared openly)
  Private key: (kept secret on server)

Your browser:
  1. Gets the server's public key
  2. Encrypts data with the public key
  3. Sends the ciphertext

The server:
  1. Receives the ciphertext
  2. Decrypts with its private key
  3. Reads the original data

Anyone intercepting the ciphertext cannot decrypt it —
they don't have the private key.
```

最常见的非对称算法是 **RSA**。其他还包括 **ECDSA**（椭圆曲线）和 **Ed25519**——如果你曾用 `ssh-keygen -t ed25519` 生成过 SSH 密钥，你就见过 Ed25519。

**非对称加密很慢。** 比对称加密慢得多。用 RSA 加密整个网页会慢得令人难以忍受。因此在实际应用中，Web 会**同时**使用两者：

1. 用非对称加密安全地交换对称密钥（解决密钥交换问题）
2. 用对称加密（AES）进行实际的数据传输（快速）

这正是你的浏览器通过 HTTPS 连接到网站时发生的情况。双方使用非对称加密协商出一个共享的对称密钥，然后使用该密钥进行后续的通信。你既获得了非对称密钥交换的安全性，又获得了对称加密的速度。

**哈希**相关但不同。哈希函数接受任意大小的输入，并产生固定大小的输出（“摘要”）。它是一个单向函数——你无法逆转哈希来获得原始输入。哈希用于：

- **密码存储**——存储哈希，而不是密码。当用户登录时，对他们的输入进行哈希并比较。
- **数据完整性**——对文件进行哈希，发送文件和哈希值。接收方对文件进行哈希并检查是否匹配。
- **数字签名**——对消息进行哈希，用私钥加密哈希值。任何拥有公钥的人都可以验证签名。

常见的哈希函数：**SHA-256**（安全，广泛使用）、**bcrypt/argon2**（专为密码设计，有意地慢）。

```bash
# Hash a string with SHA-256
echo -n "hello world" | sha256sum
# b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9

# Change one character, the hash changes completely
echo -n "hello worle" | sha256sum
# completely different hash
```

**为什么 SRE 关心这些：** 加密不是可选项——它是安全通信的基础。理解对称与非对称加密、密钥交换和哈希，有助于你调试 TLS 问题、管理证书、配置 SSH、处理密钥管理以及理解安全事件。每一个 HTTPS 连接、每一个 SSH 会话、每一次带认证令牌的 API 调用，都依赖于这些概念。

<!-- ZH_RESOURCES -->
- [Khan Academy - 密码学](https://www.khanacademy.org/computing/computer-science/cryptography) -- 类型：互动式，时长：2小时
- [Cloudflare - 什么是加密？](https://www.cloudflare.com/learning/ssl/what-is-encryption/) -- 类型：文章，时长：10分钟
- [《密码故事》- Simon Singh](https://simonsingh.net/books/the-code-book/) -- 类型：书籍，时长：不定
- [面向开发者的实用密码学（免费）](https://cryptobook.nakov.com/) -- 类型：书籍，时长：不定

<!-- ZH_UI -->
1. 解释对称加密与非对称加密的区别
2. 理解 HTTPS 为何重要以及明文 HTTP 暴露了什么
3. 描述密钥交换问题以及非对称加密如何解决它
4. 我理解了加密。Web 实际上如何用它来保护流量？
5. 我理解了基础构件——对称密钥、非对称密钥、密钥交换问题。但当我的浏览器首次连接到一个 HTTPS 站点时，这些如何发挥作用？它如何与一个从未通信过的服务器建立安全通道？
