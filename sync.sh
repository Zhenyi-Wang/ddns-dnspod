#!/bin/bash

# 同步目录到 mini 服务器的 /opt/ddns
# 排除敏感文件和不必要的文件

# 检查是否提供了排除 .env 文件的选项
EXCLUDE_ENV=true
if [[ "$1" == "--include-env" ]]; then
    EXCLUDE_ENV=false
fi

# 同步命令
SYNC_CMD="rsync -avz \
    --delete \
    --exclude '.git/' \
    --exclude '__pycache__/' \
    --exclude '.vscode/' \
    --exclude '.idea/' \
    --exclude '*.log' \
    --exclude '.DS_Store' \
    --exclude 'Thumbs.db'"

# 如果不包含 .env，则排除
if [[ "$EXCLUDE_ENV" == "true" ]]; then
    SYNC_CMD="${SYNC_CMD} \
    --exclude '.env'"
fi

# 添加源目录
SYNC_CMD="${SYNC_CMD} ."

# 执行同步
echo "开始同步目录到 mini:/opt/ddns..."
$SYNC_CMD mini:/opt/ddns

# 检查同步是否成功
if [ $? -eq 0 ]; then
    echo "同步完成！"
else
    echo "同步失败，请检查网络连接和权限。"
    exit 1
fi
