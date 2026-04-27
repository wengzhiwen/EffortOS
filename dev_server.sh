#!/bin/bash
# EffortOS 开发服务器启动脚本
# 同时启动测试 API 实例和用户体验实例

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 加载环境变量
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "=== EffortOS 开发服务器 ==="
echo ""
echo "测试 API 实例: http://localhost:5001"
echo "用户体验实例: http://localhost:5000"
echo ""

# 确保上传目录存在
mkdir -p instance/uploads

# 启动测试 API 实例（端口 5001）
FLASK_ENV=development PORT=5001 venv/bin/python run.py &
TEST_PID=$!
echo "测试 API 实例已启动 (PID: $TEST_PID, 端口: 5001)"

# 启动用户体验实例（端口 5000）
FLASK_ENV=development PORT=5000 venv/bin/python run.py &
DEV_PID=$!
echo "用户体验实例已启动 (PID: $DEV_PID, 端口: 5000)"

echo ""
echo "按 Ctrl+C 停止所有实例"

# 捕获退出信号
trap "kill $TEST_PID $DEV_PID 2>/dev/null; echo '已停止所有实例'; exit 0" SIGINT SIGTERM

wait
