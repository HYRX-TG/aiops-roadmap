---
id: rsync-backups
title: Backing Up with rsync
zone: self-hosting
edges:
  to:
    - id: cloud-backups
      question: My local backups are solid — but what about offsite?
      detail: >-
        I'm rsyncing to another machine on my network, which is great. But
        both machines are in the same building. How do I get a copy somewhere
        far away without overcomplicating things?
difficulty: 2
tags:
  - self-hosting
  - backups
  - rsync
  - linux
  - cron
category: practice
milestones:
  - Understand how rsync works (incremental, delta transfer)
  - Back up Docker volumes and config directories to another machine
  - Dump a database before backing it up (don't rsync a live DB)
  - Automate backups with cron
  - Verify you can actually restore from a backup
title_zh: "使用 rsync 进行备份"

---


rsync copies files from one place to another, and it's smart about it — it only transfers what's changed since the last run. It works over SSH, so you can back up to any machine you can SSH into. It's been around for decades, it's rock solid, and it's already installed on most Linux systems.

For file-level backups of your self-hosted services, rsync is the simplest tool that does the job well.

<!-- DEEP_DIVE -->

## What to back up

You don't need to rsync your entire server. Focus on what's irreplaceable:

```bash
# Your Docker Compose files and configs
~/docker/

# Or wherever your compose files and volumes live
/opt/services/

# Specific volume paths if you use named volumes
/var/lib/docker/volumes/
```

The key directories are your Compose files, `.env` files, and the bind-mount directories where your services store data.

## Basic rsync usage

Copy a directory to another machine on your network:

```bash
rsync -avz --delete ~/docker/ backup-server:/backups/docker/
```

What the flags do:
- `-a`: archive mode — preserves permissions, timestamps, symlinks
- `-v`: verbose — shows what's being transferred
- `-z`: compress during transfer
- `--delete`: remove files from the destination that no longer exist on the source (keeps your backup a true mirror. Be careful here though. Make sure you don't accidentally delete the whole backup)

The first run copies everything. Every run after that only transfers changed files.

## The database problem

If you rsync a PostgreSQL or MariaDB data directory while the database is running, the files might be in an inconsistent state. The backup could be corrupted.

The fix: dump the database first, then back up the dump file.

```bash
#!/bin/bash
# Dump databases before rsync
docker exec postgres pg_dumpall -U postgres > ~/backups/postgres.sql
docker exec mariadb mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" --all-databases > ~/backups/mariadb.sql

# Now rsync everything
rsync -avz --delete ~/docker/ backup-server:/backups/docker/
rsync -avz --delete ~/backups/ backup-server:/backups/dumps/
```

SQLite databases (used by Vaultwarden, many smaller apps) are more forgiving — a single-file copy is usually fine if the app isn't actively writing. But if you want to be safe, use `sqlite3 database.db ".backup backup.db"` first.

## Automating with cron

Create a backup script:

```bash
#!/bin/bash
# /usr/local/bin/backup.sh

set -euo pipefail

BACKUP_HOST="backup-server"
BACKUP_DIR="/backups/$(hostname)"

# Dump databases
docker exec postgres pg_dumpall -U postgres > /tmp/postgres.sql 2>/dev/null || true

# Sync everything
rsync -az --delete ~/docker/ "${BACKUP_HOST}:${BACKUP_DIR}/docker/"
rsync -az --delete /tmp/postgres.sql "${BACKUP_HOST}:${BACKUP_DIR}/postgres.sql"

echo "Backup completed: $(date)" >> /var/log/backup.log
```

Schedule it with cron:

```bash
crontab -e
# Run daily at 3am
0 3 * * * /usr/local/bin/backup.sh
```

Make sure SSH key authentication is set up between your server and the backup target so rsync can connect without a password prompt.

## Backup destination options

**Another machine on your network** — An old PC, a NAS, anything with SSH and disk space. This is the easiest starting point.

**An external USB drive** — Plug it in, mount it, rsync to it. Simple but manual. Good as a secondary backup, not great as your only one (you have to remember to plug it in).

**Your NAS** — If you have a Synology, QNAP, or TrueNAS box, rsync to it over SSH. Most NAS devices support SSH out of the box.

## Verify your backups

At least once, try restoring from your backup. Copy the files back, start the containers, and make sure everything works. A backup script that's been silently failing for months is worse than no backup at all — at least with no backup you know where you stand.

<!-- RESOURCES -->

- [rsync man page](https://linux.die.net/man/1/rsync) -- type: reference, time: 10min

<!-- ZH_SUMMARY -->
rsync 将文件从一个位置复制到另一个位置，而且它在这方面很智能——它只传输自上次运行以来发生更改的内容。它通过 SSH 工作，因此你可以备份到任何能通过 SSH 访问的机器。它已经存在了几十年，非常稳定可靠，而且大多数 Linux 系统上已经预装了它。

对于自托管服务的文件级备份，rsync 是能出色完成这项工作的最简单工具。

<!-- ZH_DEEP_DIVE -->
## 需要备份什么

你不需要 rsync 整个服务器。专注于那些不可替代的内容：

```bash
# 你的 Docker Compose 文件和配置
~/docker/

# 或者你的 compose 文件和卷所在的任何位置
/opt/services/

# 如果你使用命名卷，指定具体的卷路径
/var/lib/docker/volumes/
```

关键目录是你的 Compose 文件、`.env` 文件，以及服务存储数据的 bind-mount 目录。

## rsync 基本用法

将目录复制到网络上的另一台机器：

```bash
rsync -avz --delete ~/docker/ backup-server:/backups/docker/
```

各标志的作用：
- `-a`：归档模式——保留权限、时间戳、符号链接
- `-v`：详细输出——显示正在传输的内容
- `-z`：传输时压缩
- `--delete`：从目标端删除源端已不存在的文件（保持备份为真正的镜像。但要小心。确保不要意外删除整个备份）

第一次运行会复制所有内容。之后的每次运行只传输变更的文件。

## 数据库问题

如果在数据库运行时 rsync PostgreSQL 或 MariaDB 的数据目录，文件可能处于不一致状态。备份可能会损坏。

解决办法：先导出数据库，然后备份导出文件。

```bash
#!/bin/bash
# Dump databases before rsync
docker exec postgres pg_dumpall -U postgres > ~/backups/postgres.sql
docker exec mariadb mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" --all-databases > ~/backups/mariadb.sql

# Now rsync everything
rsync -avz --delete ~/docker/ backup-server:/backups/docker/
rsync -avz --delete ~/backups/ backup-server:/backups/dumps/
```

SQLite 数据库（Vaultwarden 和许多小型应用使用）更宽容——如果应用没有在主动写入，单文件复制通常没问题。但如果你想更稳妥，先使用 `sqlite3 database.db ".backup backup.db"`。

## 使用 cron 自动化

创建一个备份脚本：

```bash
#!/bin/bash
# /usr/local/bin/backup.sh

set -euo pipefail

BACKUP_HOST="backup-server"
BACKUP_DIR="/backups/$(hostname)"

# Dump databases
docker exec postgres pg_dumpall -U postgres > /tmp/postgres.sql 2>/dev/null || true

# Sync everything
rsync -az --delete ~/docker/ "${BACKUP_HOST}:${BACKUP_DIR}/docker/"
rsync -az --delete /tmp/postgres.sql "${BACKUP_HOST}:${BACKUP_DIR}/postgres.sql"

echo "Backup completed: $(date)" >> /var/log/backup.log
```

用 cron 安排它：

```bash
crontab -e
# Run daily at 3am
0 3 * * * /usr/local/bin/backup.sh
```

确保你的服务器和备份目标之间已设置 SSH 密钥认证，这样 rsync 无需密码提示即可连接。

## 备份目标选项

**网络上的另一台机器**——一台旧 PC、一个 NAS，任何有 SSH 和磁盘空间的东西。这是最简单的起点。

**外置 USB 驱动器**——插上、挂载、rsync 到它。简单但手动。适合作为辅助备份，不太适合作为唯一备份（你必须记得插上它）。

**你的 NAS**——如果你有 Synology、QNAP 或 TrueNAS 设备，通过 SSH rsync 到它。大多数 NAS 设备开箱即支持 SSH。

## 验证你的备份

至少尝试一次从备份恢复。将文件复制回来，启动容器，确保一切正常。一个已经静默失败数月的备份脚本比没有备份更糟——至少没有备份时你知道自己的处境。

<!-- ZH_RESOURCES -->
- [rsync 手册页](https://linux.die.net/man/1/rsync) -- 类型：参考，时间：10分钟

<!-- ZH_UI -->
1. 理解 rsync 的工作原理（增量、差异传输）
2. 将 Docker 卷和配置目录备份到另一台机器
3. 备份前先导出数据库（不要对运行中的数据库直接 rsync）
4. 用 cron 自动化备份
5. 验证你确实能从备份中恢复
6. 我的本地备份很可靠——但异地备份呢？
7. 我正在用 rsync 备份到网络上的另一台机器，这很好。但两台机器在同一栋楼里。如何在不把事情搞复杂的前提下，把一份副本放到很远的地方？
