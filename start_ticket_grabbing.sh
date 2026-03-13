#!/bin/bash
# 大麦抢票 - 抢票启动脚本
# 使用方法: ./start_ticket_grabbing.sh

echo "🎫 启动大麦抢票脚本..."

# 设置Android环境变量（允许外部预先传入，默认使用当前用户目录）
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$ANDROID_HOME}"

# 检查Appium服务器是否运行
if ! curl -s http://127.0.0.1:4723/status > /dev/null; then
    echo "❌ Appium服务器未运行"
    echo "   请先运行: ./start_appium.sh"
    exit 1
fi

echo "✅ Appium服务器运行正常"

# 检查配置文件
if [ ! -f "damai_appium/config.jsonc" ]; then
    echo "❌ 配置文件不存在: damai_appium/config.jsonc"
    exit 1
fi

echo "✅ 配置文件存在"

# 显示当前配置
echo "📋 当前配置:"
echo "   $(cat damai_appium/config.jsonc | grep -E '"keyword"|"city"|"users"' | head -3)"

# 开始抢票
# 进入脚本目录
cd damai_appium

echo "🚀 开始抢票..."
echo "   请确保："
echo "   1. 大麦APP已打开"
echo "   2. 已搜索到目标演出"
echo "   3. 已进入演出详情页面"
echo ""

# 运行抢票脚本
if command -v poetry >/dev/null 2>&1; then
    poetry run python damai_app_v2.py
else
    python3 damai_app_v2.py
fi
