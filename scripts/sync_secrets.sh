#!/bin/bash
# 从 .env 文件同步 secrets 到 GitHub Actions
# 用法: ./scripts/sync_secrets.sh

set -e

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "错误: 找不到 $ENV_FILE 文件"
    exit 1
fi

# 检查 gh CLI 是否已登录
if ! gh auth status &>/dev/null; then
    echo "请先登录 GitHub CLI: gh auth login"
    exit 1
fi

echo "开始同步 secrets 到 GitHub..."

# 读取 .env 文件，跳过注释和空行
while IFS= read -r line || [ -n "$line" ]; do
    # 跳过空行和注释
    [[ -z "$line" || "$line" =~ ^# ]] && continue

    # 解析 key=value
    key="${line%%=*}"
    value="${line#*=}"

    # 跳过无效行
    [[ -z "$key" || -z "$value" ]] && continue

    echo "设置 $key..."
    gh secret set "$key" --body "$value"
done < "$ENV_FILE"

echo "同步完成！"
echo ""
echo "验证已设置的 secrets:"
gh secret list
