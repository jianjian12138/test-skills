#!/usr/bin/env bash
# 安装 QA skills 套件到目标 agent 技能目录（跨 agent 兼容）
# 用法：
#   ./install.sh                          # 默认 flavor=workbuddy，装到 ./.workbuddy/skills
#   ./install.sh --flavor claude         # 装到 ./.claude/skills（Claude Code / Cursor 等）
#   ./install.sh --flavor generic        # 装到 ./skills
#   ./install.sh --target /p/a/th        # 显式指定目标目录（覆盖 flavor 推导）
set -e

FLAVOR="workbuddy"
TARGET=""
while [ $# -gt 0 ]; do
  case "$1" in
    --flavor) FLAVOR="$2"; shift 2;;
    --target) TARGET="$2"; shift 2;;
    -h|--help) echo "用法: ./install.sh [--flavor workbuddy|claude|generic] [--target <dir>]"; exit 0;;
    *) echo "未知参数: $1"; exit 1;;
  esac
done

# 未显式指定 target 时，按 flavor 推导目标目录
if [ -z "$TARGET" ]; then
  case "$FLAVOR" in
    workbuddy) TARGET="./.workbuddy/skills";;
    claude)    TARGET="./.claude/skills";;
    generic)   TARGET="./skills";;
    *) echo "未知 flavor: $FLAVOR（支持 workbuddy|claude|generic）"; exit 1;;
  esac
fi

SRC="$(cd "$(dirname "$0")" && pwd)/.workbuddy/skills"
if [ ! -d "$SRC" ]; then
  echo "❌ 未找到源技能目录: $SRC"; exit 1
fi

# R-10：源与目标真实路径相等守卫（默认 flavor 在仓库根执行时 SRC==TARGET，原地复制会失败）
SRC_REAL="$(cd "$SRC" && pwd)"
TARGET_PARENT="$(cd "$(dirname "$TARGET")" 2>/dev/null && pwd)"
TARGET_REAL="$TARGET_PARENT/$(basename "$TARGET")"
if [ "$SRC_REAL" = "$TARGET_REAL" ]; then
  echo "❌ 源目录与目标目录相同（$SRC_REAL），无法原地复制。"
  echo "   请显式指定目标： ./install.sh --target /path/to/agent/skills"
  echo "   或换用其他 flavor： ./install.sh --flavor generic   # 装到 ./skills"
  exit 1
fi

mkdir -p "$TARGET"
cp -r "$SRC"/. "$TARGET"/
# 清理维护者工具与缓存，保持分发包干净（跨 agent 仅需技能目录）
find "$TARGET" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
rm -f "$TARGET/build_registry.py" "$TARGET/REGISTRY.json"
rm -f "$TARGET/qa-orchestrator/scripts/check_drift.py"
rm -rf "$TARGET/tools"
N=$(find "$TARGET" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l)
echo "✅ 已安装 QA skills 套件到: $TARGET (flavor=$FLAVOR)"
echo "   共 $N 个技能目录（含 qa-orchestrator 编排与各阶段技能）"
echo "   单技能均可独立使用；重新加载项目/agent 即可启用。"
echo "   CI 门禁接入见 README「CI 门禁」章节；编排为可选层（默认不装也可逐技能调用）。"
