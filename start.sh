#!/bin/bash
# 启动 2026世界杯项目（前后端同时启动）— FastAPI + Vue3

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "=========================================="
echo "  2026世界杯 - 启动中..."
echo "=========================================="

# 检查后端环境
if [ ! -f "$BACKEND_DIR/run.py" ]; then
    echo "❌ 错误: 找不到 run.py"
    exit 1
fi

# 检查前端目录
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ 错误: 找不到 frontend 目录"
    exit 1
fi

# 激活虚拟环境
if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_CMD="$SCRIPT_DIR/venv/bin/python"
elif [ -f "$SCRIPT_DIR/venv/bin/python3" ]; then
    PYTHON_CMD="$SCRIPT_DIR/venv/bin/python3"
else
    echo "❌ 错误: 找不到虚拟环境"
    exit 1
fi

# 启动后端 (FastAPI / uvicorn)
echo ""
echo "🚀 启动后端服务 (FastAPI)..."
cd "$BACKEND_DIR"
$PYTHON_CMD run.py &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 检查后端是否启动成功
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ 后端启动失败"
    exit 1
fi

# 启动前端 (Vue/Vite dev server)
echo ""
echo "🚀 启动前端服务 (Vue/Vite)..."
cd "$FRONTEND_DIR"

# 检查是否已安装依赖
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "📦 首次运行，安装前端依赖..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"

echo ""
echo "=========================================="
echo "  ✅ 服务已启动!"
echo "=========================================="
echo ""
echo "  📍 访问地址:"
echo "     后端 API:  http://127.0.0.1:6000"
echo "     前端页面: http://127.0.0.1:6018"
echo "     API 文档: http://127.0.0.1:6000/docs"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "=========================================="

# 捕获 Ctrl+C 信号，停止所有进程
cleanup() {
    echo ""
    echo "🛑 停止服务..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ 服务已停止"
    exit 0
}
trap cleanup SIGINT SIGTERM

# 等待所有子进程
wait
