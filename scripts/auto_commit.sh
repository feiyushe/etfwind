#!/bin/bash
# 自动生成详细的 git commit 信息
# v1.0

# 获取变更的文件
changed_files=$(git diff --cached --name-only 2>/dev/null)
if [ -z "$changed_files" ]; then
    git add -A
    changed_files=$(git diff --cached --name-only 2>/dev/null)
fi

# 无变更则退出
[ -z "$changed_files" ] && exit 0

# 生成文件列表
file_list=$(echo "$changed_files" | head -5 | tr '\n' ', ' | sed 's/,$//')
file_count=$(echo "$changed_files" | wc -l | tr -d ' ')

# 获取变更摘要
diff_stat=$(git diff --cached --stat | tail -1)

# 构建提交信息
if [ "$file_count" -eq 1 ]; then
    msg="auto: 修改 $file_list"
else
    msg="auto: 修改 ${file_count} 个文件 ($file_list)"
fi

# 添加变更统计
body="$diff_stat"

# 提交
git commit -m "$msg" -m "$body" --no-verify 2>/dev/null || true
