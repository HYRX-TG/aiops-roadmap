---
id: cloud-backups
title: 'Offsite Backups: Getting a Copy Off-Site'
zone: self-hosting
difficulty: 1
tags:
  - self-hosting
  - backups
  - offsite
  - cloud
  - restic
  - rclone
  - backblaze
category: concept
milestones:
  - Understand why offsite backups matter (the "1" in 3-2-1)
  - Know the major options (Backblaze B2, rsync.net, Hetzner Storage Box)
  - Encrypt your backups before uploading
  - Set up automated offsite backups with restic or rclone
  - Test restoring from an offsite backup
title_zh: "异地备份：将副本保存至异地"

---


Local backups protect you from disk failures, accidental deletions, and botched upgrades. They don't protect you from a power surge that fries everything on your desk, a flood, a fire, or a break-in. For that, you need a copy somewhere physically separate.

The good news: offsite backup for self-hosters is cheap and straightforward. Most homelab setups have relatively small amounts of critical data — gigabytes, not terabytes — and cloud storage pricing has gotten very reasonable.

<!-- DEEP_DIVE -->

## Where to store offsite backups

**Backblaze B2** — $6/TB/month for storage, $0.01/GB for downloads. The most popular choice for self-hosters. S3-compatible API, so it works with nearly every backup tool. Free egress through their CDN partnership with Cloudflare. For most homelabs, you're looking at well under $1/month.

**Hetzner Storage Box** — Starts at a few euros/month for 1TB. Accessible via SSH/SFTP/rsync/SMB. Based in Europe. Simple pricing, no per-request fees. You can rsync directly to it without any special tooling.

**rsync.net** — SSH-based storage, priced per GB. More expensive than B2 but dead simple — it's just a remote filesystem you rsync to. They also offer special pricing for restic/borg users.

**A friend's house** — Seriously. If you have a friend who also self-hosts, trade backup space. You rsync to a machine at their place, they rsync to yours. Free, offsite, and you both benefit.

## Encrypt before uploading

Never upload unencrypted backups to a third party. Your Vaultwarden data, your personal photos, your configs with passwords in `.env` files — all of that should be encrypted before it leaves your network.

The tools below handle encryption automatically. Don't roll your own.

## restic — the recommended approach

restic is a backup program that handles encryption, deduplication, and incremental backups. It works with local paths, SFTP, and S3-compatible storage (including Backblaze B2).

```bash
# Install
sudo apt install restic

# Initialize a repository on Backblaze B2
export B2_ACCOUNT_ID="your-account-id"
export B2_ACCOUNT_KEY="your-account-key"
restic -r b2:your-bucket-name:backups init

# Run a backup
restic -r b2:your-bucket-name:backups backup ~/docker/ /tmp/postgres.sql

# List snapshots
restic -r b2:your-bucket-name:backups snapshots

# Restore
restic -r b2:your-bucket-name:backups restore latest --target /tmp/restore/
```

restic encrypts everything client-side with a password you set during `init`. Even if someone gets access to your B2 bucket, they can't read the data.

After the first full backup, subsequent runs are fast — restic deduplicates at the block level, so only changed chunks are uploaded.

## rclone — the Swiss Army knife

rclone is a file sync tool that supports dozens of cloud providers. It's not a backup tool per se — it doesn't do deduplication or snapshotting — but it's great for syncing files to cloud storage.

```bash
# Install
sudo apt install rclone

# Configure a remote (interactive)
rclone config

# Sync a directory to B2
rclone sync ~/docker/ b2:your-bucket/docker/ --b2-hard-delete

# With encryption (using rclone crypt)
rclone sync ~/docker/ secret-b2:docker/
```

rclone's `crypt` overlay encrypts filenames and content transparently. You set it up once during `rclone config` and then use the encrypted remote like any other.

Use rclone if you want a simple mirror of your files in the cloud. Use restic if you want versioned snapshots with deduplication.

## Automating offsite backups

Same pattern as local backups — a script and a cron job:

```bash
#!/bin/bash
# /usr/local/bin/offsite-backup.sh

export B2_ACCOUNT_ID="your-account-id"
export B2_ACCOUNT_KEY="your-account-key"
REPO="b2:your-bucket-name:backups"

# Run restic backup
restic -r "$REPO" backup ~/docker/ /tmp/postgres.sql --quiet

# Prune old snapshots: keep 7 daily, 4 weekly, 6 monthly
restic -r "$REPO" forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune --quiet
```

```bash
crontab -e
# Run after local backup completes, e.g., 4am
0 4 * * * /usr/local/bin/offsite-backup.sh
```

## How much does it cost?

For reference, here's what typical self-hosted data costs on Backblaze B2:

| Data size | Monthly cost |
|---|---|
| 10 GB | ~$0.06 |
| 50 GB | ~$0.30 |
| 100 GB | ~$0.60 |
| 500 GB | ~$3.00 |

Most self-hosters (excluding media libraries) have well under 50 GB of critical data. If you're backing up a large media library, you might want to be selective — back up the irreplaceable stuff (photos, documents) and accept that movies and TV shows can be re-downloaded.

<!-- RESOURCES -->

- [restic Documentation](https://restic.readthedocs.io/) -- type: reference, time: ongoing
- [rclone Documentation](https://rclone.org/docs/) -- type: reference, time: ongoing
- [Backblaze B2 Pricing](https://www.backblaze.com/cloud-storage/pricing) -- type: reference, time: 5min

<!-- ZH_SUMMARY -->
本地备份能保护你免受磁盘故障、误删除和升级失败的影响，但无法保护你免受电涌烧毁桌面上所有设备、洪水、火灾或入室盗窃的威胁。为此，你需要在物理上分离的某处保留一份副本。

好消息是：对自托管者而言，异地备份既便宜又简单。大多数 homelab 配置的关键数据量相对较小——是 GB 级而非 TB 级——而且云存储定价已经变得非常合理。

<!-- ZH_DEEP_DIVE -->
## 异地备份的存储位置

**Backblaze B2** — 存储费用为 $6/TB/月，下载费用为 $0.01/GB。这是自托管用户最热门的选择。它提供兼容 S3 的 API，因此几乎能与所有备份工具配合使用。通过与 Cloudflare 的 CDN 合作，可以免费出站。对于大多数家庭实验室来说，每月费用远低于 $1。

**Hetzner Storage Box** — 1TB 起价每月几欧元。可通过 SSH/SFTP/rsync/SMB 访问。位于欧洲。定价简单，无按请求收费。你可以直接用 rsync 同步到它，无需任何特殊工具。

**rsync.net** — 基于 SSH 的存储，按 GB 计价。比 B2 贵，但极其简单——它就是一个你可以 rsync 到的远程文件系统。他们还为 restic/borg 用户提供特价。

**朋友家** — 说真的。如果你有朋友也在自托管，可以交换备份空间。你 rsync 到他们那里的机器，他们 rsync 到你的机器。免费、异地，而且双方都受益。

## 上传前加密

绝不要将未加密的备份上传到第三方。你的 Vaultwarden 数据、个人照片、包含 `.env` 文件中密码的配置——所有这些都应该在离开你的网络之前加密。

下面的工具会自动处理加密。不要自己造轮子。

## restic — 推荐方案

restic 是一个备份程序，负责处理加密、去重和增量备份。它支持本地路径、SFTP 以及兼容 S3 的存储（包括 Backblaze B2）。

```bash
# Install
sudo apt install restic

# Initialize a repository on Backblaze B2
export B2_ACCOUNT_ID="your-account-id"
export B2_ACCOUNT_KEY="your-account-key"
restic -r b2:your-bucket-name:backups init

# Run a backup
restic -r b2:your-bucket-name:backups backup ~/docker/ /tmp/postgres.sql

# List snapshots
restic -r b2:your-bucket-name:backups snapshots

# Restore
restic -r b2:your-bucket-name:backups restore latest --target /tmp/restore/
```

restic 使用你在 `init` 时设置的密码在客户端加密所有内容。即使有人获取了你的 B2 存储桶访问权限，他们也无法读取数据。

首次完整备份后，后续运行会很快——restic 在块级别进行去重，因此只上传更改过的块。

## rclone — 瑞士军刀

rclone 是一个文件同步工具，支持数十种云提供商。它本身不是备份工具——它不做去重或快照——但它非常适合将文件同步到云存储。

```bash
# Install
sudo apt install rclone

# Configure a remote (interactive)
rclone config

# Sync a directory to B2
rclone sync ~/docker/ b2:your-bucket/docker/ --b2-hard-delete

# With encryption (using rclone crypt)
rclone sync ~/docker/ secret-b2:docker/
```

rclone 的 `crypt` 覆盖层会透明地加密文件名和内容。你在 `rclone config` 期间设置一次，然后就可以像使用其他远程一样使用加密远程。

如果你想要云中文件的简单镜像，请使用 rclone。如果你想要带去重的版本化快照，请使用 restic。

## 自动化异地备份

与本地备份相同的模式——一个脚本和一个 cron 任务：

```bash
#!/bin/bash
# /usr/local/bin/offsite-backup.sh

export B2_ACCOUNT_ID="your-account-id"
export B2_ACCOUNT_KEY="your-account-key"
REPO="b2:your-bucket-name:backups"

# Run restic backup
restic -r "$REPO" backup ~/docker/ /tmp/postgres.sql --quiet

# Prune old snapshots: keep 7 daily, 4 weekly, 6 monthly
restic -r "$REPO" forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune --quiet
```

```bash
crontab -e
# Run after local backup completes, e.g., 4am
0 4 * * * /usr/local/bin/offsite-backup.sh
```

## 费用是多少？

作为参考，以下是典型自托管数据在 Backblaze B2 上的费用：

| 数据大小 | 每月费用 |
|---|---|
| 10 GB | ~$0.06 |
| 50 GB | ~$0.30 |
| 100 GB | ~$0.60 |
| 500 GB | ~$3.00 |

大多数自托管用户（不包括媒体库）的关键数据远低于 50 GB。如果你要备份大型媒体库，可能需要有所选择——备份不可替代的内容（照片、文档），并接受电影和电视节目可以重新下载的事实。

<!-- ZH_RESOURCES -->
- [restic 文档](https://restic.readthedocs.io/) -- 类型：参考，时间：持续
- [rclone 文档](https://rclone.org/docs/) -- 类型：参考，时间：持续
- [Backblaze B2 定价](https://www.backblaze.com/cloud-storage/pricing) -- 类型：参考，时间：5 分钟

<!-- ZH_UI -->
1. 理解异地备份的重要性（3-2-1 原则中的“1”）
2. 了解主要可选方案（Backblaze B2、rsync.net、Hetzner Storage Box）
3. 上传前先加密备份
4. 使用 restic 或 rclone 设置自动化异地备份
5. 测试从异地备份恢复
