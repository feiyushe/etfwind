# Mac Mini M4 Pro Bot Farm 运行方案

## 硬件配置

| 项目 | 规格 |
|------|------|
| 机型 | Mac Mini M4 Pro |
| CPU | 14核（12性能+2能效） |
| 内存 | 64GB |
| 存储 | 4TB SSD |
| 网络 | 10Gb 以太网 |

## 容量规划

| 资源 | 总量 | 单 VM 分配 | 可开 VM 数 |
|------|------|-----------|-----------|
| 内存 | 64GB | 8GB | 6-7 个 |
| CPU | 14核 | 2核 | 7 个 |
| 存储 | 4TB | 60GB | 60+ 个 |

**建议稳定运行 6 个 VM**，留余量给宿主机。

---

## 工具栈

### 1. 虚拟化：Tart

macOS 原生虚拟化，完整 CLI 支持。

```bash
# 安装
brew install cirruslabs/cli/tart
```

### 2. Bot 框架：ClawdBot (Moltbot)

Claude 驱动的自动化 bot。

```bash
# 在每个 VM 内安装
git clone https://github.com/clawdbot/clawdbot.git
cd clawdbot
npm install
```

### 3. 浏览器自动化：Playwright

```bash
npm install playwright
npx playwright install
```

### 4. 进程管理：PM2

```bash
npm install -g pm2
```

### 5. 任务调度：Redis + BullMQ（可选）

```bash
brew install redis
npm install bullmq
```

---

## 目录结构

```
~/bot-farm/
├── vms/                    # VM 镜像存储
│   ├── base-image/         # 基础镜像
│   └── instances/          # 运行实例
├── scripts/                # 管理脚本
│   ├── setup-vm.sh         # VM 初始化
│   ├── start-all.sh        # 启动所有 VM
│   ├── stop-all.sh         # 停止所有 VM
│   └── status.sh           # 查看状态
├── config/                 # 配置文件
│   ├── vm-config.json      # VM 配置
│   └── bot-config.json     # Bot 配置
└── logs/                   # 日志目录
```

---

## 第一部分：环境搭建

### 1.1 安装 Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 1.2 安装 Tart

```bash
brew install cirruslabs/cli/tart
```

### 1.3 拉取 macOS 基础镜像

```bash
# 拉取 macOS Sonoma 镜像（约 15GB）
tart clone ghcr.io/cirruslabs/macos-sonoma-base:latest base-sonoma
```

### 1.4 创建 VM 实例

```bash
# 创建 6 个 VM 实例
for i in {1..6}; do
  tart clone base-sonoma bot-vm-$i
done
```

---

## 第二部分：VM 配置

### 2.1 单个 VM 资源配置

```bash
# 设置 VM 资源（8GB 内存，2 CPU）
tart set bot-vm-1 --memory 8192 --cpu 2
```

### 2.2 批量配置脚本

创建 `scripts/configure-vms.sh`：

```bash
#!/bin/bash

for i in {1..6}; do
  echo "配置 bot-vm-$i..."
  tart set bot-vm-$i --memory 8192 --cpu 2
done

echo "配置完成"
```

### 2.3 启动 VM

```bash
# 启动单个 VM（无头模式）
tart run bot-vm-1 --no-graphics &

# 通过 SSH 连接
ssh admin@$(tart ip bot-vm-1)
```

---

## 第三部分：VM 内环境初始化

在每个 VM 内执行以下步骤。

### 3.1 安装基础工具

```bash
# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Node.js
brew install node

# 安装 Git
brew install git
```

### 3.2 安装 ClawdBot

```bash
# 克隆仓库
git clone https://github.com/clawdbot/clawdbot.git ~/clawdbot
cd ~/clawdbot

# 安装依赖
npm install

# 安装 Playwright 浏览器
npx playwright install chromium
```

### 3.3 配置 Claude API

```bash
# 创建配置文件
cat > ~/.clawdbot/config.json << 'EOF'
{
  "api_key": "your-claude-api-key",
  "model": "claude-sonnet-4-20250514",
  "memory_path": "~/.clawdbot/memory"
}
EOF
```

### 3.4 创建 VM 初始化脚本

保存为 `scripts/init-vm.sh`，在 VM 内运行：

```bash
#!/bin/bash

echo "=== 初始化 Bot VM ==="

# 安装 Homebrew
if ! command -v brew &> /dev/null; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# 安装依赖
brew install node git

# 克隆 ClawdBot
if [ ! -d ~/clawdbot ]; then
  git clone https://github.com/clawdbot/clawdbot.git ~/clawdbot
fi

cd ~/clawdbot
npm install
npx playwright install chromium

echo "=== 初始化完成 ==="
```

---

## 第四部分：管理脚本

### 4.1 启动所有 VM

`scripts/start-all.sh`：

```bash
#!/bin/bash

echo "启动所有 Bot VM..."

for i in {1..6}; do
  echo "启动 bot-vm-$i..."
  tart run bot-vm-$i --no-graphics &
  sleep 5  # 等待 VM 启动
done

echo "所有 VM 已启动"
```

### 4.2 停止所有 VM

`scripts/stop-all.sh`：

```bash
#!/bin/bash

echo "停止所有 Bot VM..."

for i in {1..6}; do
  echo "停止 bot-vm-$i..."
  tart stop bot-vm-$i
done

echo "所有 VM 已停止"
```

### 4.3 查看状态

`scripts/status.sh`：

```bash
#!/bin/bash

echo "=== Bot Farm 状态 ==="
echo ""

for i in {1..6}; do
  IP=$(tart ip bot-vm-$i 2>/dev/null)
  if [ -n "$IP" ]; then
    echo "bot-vm-$i: 运行中 ($IP)"
  else
    echo "bot-vm-$i: 已停止"
  fi
done
```

### 4.4 批量执行命令

`scripts/exec-all.sh`：

```bash
#!/bin/bash

CMD="$1"

if [ -z "$CMD" ]; then
  echo "用法: ./exec-all.sh <command>"
  exit 1
fi

for i in {1..6}; do
  IP=$(tart ip bot-vm-$i 2>/dev/null)
  if [ -n "$IP" ]; then
    echo "=== bot-vm-$i ==="
    ssh admin@$IP "$CMD"
  fi
done
```

---

## 第五部分：Bot 运行管理

### 5.1 使用 PM2 管理 Bot 进程

在每个 VM 内：

```bash
# 安装 PM2
npm install -g pm2

# 启动 ClawdBot
cd ~/clawdbot
pm2 start npm --name "clawdbot" -- start

# 查看状态
pm2 status

# 查看日志
pm2 logs clawdbot
```

### 5.2 PM2 配置文件

创建 `ecosystem.config.js`：

```javascript
module.exports = {
  apps: [{
    name: 'clawdbot',
    cwd: '~/clawdbot',
    script: 'npm',
    args: 'start',
    autorestart: true,
    max_restarts: 10,
    restart_delay: 5000,
    env: {
      NODE_ENV: 'production'
    }
  }]
}
```

### 5.3 开机自启动

```bash
pm2 startup
pm2 save
```

---

## 第六部分：监控与日志

### 6.1 宿主机监控脚本

`scripts/monitor.sh`：

```bash
#!/bin/bash

while true; do
  clear
  echo "=== Bot Farm Monitor ==="
  echo "时间: $(date)"
  echo ""

  # 系统资源
  echo "--- 宿主机资源 ---"
  echo "内存: $(memory_pressure | head -1)"
  echo ""

  # VM 状态
  echo "--- VM 状态 ---"
  for i in {1..6}; do
    IP=$(tart ip bot-vm-$i 2>/dev/null)
    if [ -n "$IP" ]; then
      STATUS=$(ssh -o ConnectTimeout=2 admin@$IP "pm2 jlist 2>/dev/null | jq -r '.[0].pm2_env.status'" 2>/dev/null)
      echo "bot-vm-$i: $IP | Bot: ${STATUS:-unknown}"
    else
      echo "bot-vm-$i: 已停止"
    fi
  done

  sleep 30
done
```

### 6.2 日志收集

```bash
# 收集所有 VM 的日志到宿主机
for i in {1..6}; do
  IP=$(tart ip bot-vm-$i 2>/dev/null)
  if [ -n "$IP" ]; then
    scp admin@$IP:~/.pm2/logs/*.log ~/bot-farm/logs/vm-$i/
  fi
done
```

---

## 第七部分：常用操作

### 快速参考

| 操作 | 命令 |
|------|------|
| 启动所有 VM | `./scripts/start-all.sh` |
| 停止所有 VM | `./scripts/stop-all.sh` |
| 查看状态 | `./scripts/status.sh` |
| 进入 VM | `ssh admin@$(tart ip bot-vm-1)` |
| 批量执行 | `./scripts/exec-all.sh "pm2 status"` |
| 监控面板 | `./scripts/monitor.sh` |

### 故障排查

```bash
# VM 无法启动
tart delete bot-vm-1
tart clone base-sonoma bot-vm-1

# Bot 崩溃
ssh admin@$(tart ip bot-vm-1) "pm2 restart clawdbot"

# 内存不足
tart stop bot-vm-6  # 减少 VM 数量
```

---

## 扩展：多机集群

如果后续增加更多 Mac Mini，可以使用以下架构：

```
┌─────────────────────────────────────────────────┐
│                  调度服务器                       │
│              (Redis + BullMQ)                   │
└─────────────────┬───────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
      ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Mac #1  │ │ Mac #2  │ │ Mac #3  │
│ 6 VMs   │ │ 6 VMs   │ │ 6 VMs   │
└─────────┘ └─────────┘ └─────────┘
```

---

## 注意事项

1. **API Key 管理**：每个 VM 使用独立的 Claude API Key，避免限流
2. **网络隔离**：考虑使用代理池，避免 IP 被封
3. **资源监控**：定期检查内存和 CPU 使用率
4. **备份**：定期备份 VM 镜像和配置
5. **安全**：不要在 VM 内存储敏感信息

---

## 下一步

1. 到货后安装 macOS 和基础工具
2. 按本文档配置 Tart 和 VM
3. 测试单个 VM 运行 ClawdBot
4. 逐步扩展到 6 个 VM
5. 根据实际情况调整资源分配
