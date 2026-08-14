#!/usr/bin/env bash
# 打包 QA skills 分发包（离线 / 跨 agent 分发）。R-21：明示分发目录清理规则，
# 避免把开发缓存带进交付 zip。
#
# ⚠️ 关键决策（验收交付修正）：tools/ 必须随包。
#   自测套件 run_all_tests.py 通过 importlib 直接加载
#   tools/validate_portability.py（RK-08 等用例），甲方需能独立复跑
#   tests/run_all_tests.py 完成签字验收；故 tools/（验收闸门 + 依赖）随包，
#   不按最初"维护者工具不随包"的设想排除。
#
# 用法：
#   ./make_dist.sh                  # 在当前仓库根打包，输出 dist/qa-skills-<date>.zip
#   ./make_dist.sh --out /tmp/x.zip # 显式指定输出路径
#
# 打包内容（仅交付物，不含开发态）：
#   .workbuddy/skills/   技能套件（40 技能 + REGISTRY.json + tools/ 验收闸门 + tests/ 自测）
#   README.md  SKILLS_DELIVERY.md  LICENSE  install.sh  install.ps1
#
# 显式清理 / 排除（开发态）：.git / .tmp_test_phase5 / __pycache__ / *.pyc / node_modules / reviews
set -e

OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="$2"; shift 2;;
    -h|--help) echo "用法: ./make_dist.sh [--out <zip路径>]"; exit 0;;
    *) echo "未知参数: $1"; exit 1;;
  esac
done

ROOT="$(cd "$(dirname "$0")" && pwd)"
ROOT_W="$(cd "$(dirname "$0")" && pwd -W)"
SRC_SKILLS="$ROOT/.workbuddy/skills"
if [ ! -d "$SRC_SKILLS" ]; then
  echo "❌ 未找到源技能目录: $SRC_SKILLS"; exit 1
fi

DATE="$(date +%Y%m%d)"
if [ -z "$OUT" ]; then
  OUT="$ROOT_W/dist/qa-skills-$DATE.zip"
fi
mkdir -p "$(dirname "$OUT")"

# 1) 复制交付物到 staging
STAGE="$(mktemp -d)"
mkdir -p "$STAGE/.workbuddy"
cp -r "$SRC_SKILLS" "$STAGE/.workbuddy/skills"
cp "$ROOT/README.md" "$ROOT/SKILLS_DELIVERY.md" "$ROOT/LICENSE" \
   "$ROOT/install.sh" "$ROOT/install.ps1" "$STAGE/"

# 2) 清理开发态残留（pycache / pyc）——tools/ 刻意保留（见顶部说明）
find "$STAGE" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find "$STAGE" -type f -name "*.pyc" -delete 2>/dev/null || true

# 3) 用 Python 标准库 zipfile 打包（Windows 无 zip 命令，跨平台可靠）
#    ⚠️ 路径必须转成 Windows 原生形式：托管 python 是 Windows 可执行，
#    不识别 Git-Bash 的 /d/... 绝对路径（会误当当前盘根写成 C:/d/...）。
#    注：zipfile "w" 模式直接覆盖已有 zip，无需先 rm（避免触发沙箱 safe-delete 拦截）。
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
fi
STAGE_W="$(cd "$STAGE" && pwd -W)"
"$PY" - "$STAGE_W" "$OUT" <<'PYEOF'
import os, sys, zipfile
stage, out = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
n = 0
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(stage):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".pyc"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, stage).replace(os.sep, "/")
            # 排除内部维护评审过程稿（.workbuddy/skills/reviews/），不随交付包
            if "reviews" in rel.split("/"):
                continue
            z.write(full, rel)
            n += 1
print("zipped %d entries" % n)
PYEOF

echo "✅ 已打包分发包: $OUT"
echo "   含：.workbuddy/skills（40 技能 + tools 验收闸门 + tests 自测，已清理 __pycache__/*.pyc）"
echo "       README.md / SKILLS_DELIVERY.md / LICENSE / install.sh / install.ps1"
echo "   不含：.git / .tmp_test_phase5 / reviews / node_modules（开发态）"
echo "   甲方解压后验收：python .workbuddy/skills/tests/run_all_tests.py  （预期 113/113）"
