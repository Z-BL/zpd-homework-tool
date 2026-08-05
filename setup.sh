#!/bin/bash
set -e

echo "============================================================"
echo "  ZPD 精准作业设计工具 — 一键初始化"
echo "============================================================"
echo ""

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo "[ERROR] 未找到 uv，请先安装 uv"
    echo "        安装命令：curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "        或访问：https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi
echo "[OK] uv 已就绪"

# 创建虚拟环境
echo "[1/3] 创建虚拟环境..."
uv venv
echo "[OK] 虚拟环境已创建"

# 安装依赖
echo "[2/3] 安装 Python 依赖..."
uv pip install -r requirements.txt
echo "[OK] 依赖已安装"

# 检查 .env
echo "[3/3] 检查配置文件..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[WARN] 已创建 .env 文件，请编辑填入你的 DeepSeek API Key"
    echo "       文件位置：$(pwd)/.env"
else
    echo "[OK] .env 文件已存在"
fi

echo ""
echo "============================================================"
echo "  初始化完成！"
echo ""
echo "  启动方式："
echo "    .venv/bin/python app.py"
echo ""
echo "  浏览器访问：http://localhost:5000"
echo "============================================================"
