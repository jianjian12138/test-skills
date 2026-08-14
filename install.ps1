# 安装 QA skills 套件到目标 agent 技能目录（Windows PowerShell，跨 agent 兼容）
# 用法：
#   .\install.ps1                        # 默认 flavor=workbuddy，装到 .\.workbuddy\skills
#   .\install.ps1 -Flavor claude        # 装到 .\.claude\skills（Claude Code / Cursor 等）
#   .\install.ps1 -Flavor generic       # 装到 .\skills
#   .\install.ps1 -Target D:\proj       # 显式指定目标根目录下的技能目录
param(
  [string]$Flavor = "workbuddy",
  [string]$Target = ""
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$Src = Join-Path $Repo ".workbuddy\skills"
if (-not (Test-Path $Src)) {
  Write-Error "未找到源技能目录: $Src"
  exit 1
}

# 未显式指定 target 时，按 flavor 推导目标目录
if ([string]::IsNullOrEmpty($Target)) {
  switch ($Flavor) {
    "workbuddy" { $Target = ".\.workbuddy\skills" }
    "claude"    { $Target = ".\.claude\skills" }
    "generic"   { $Target = ".\skills" }
    default     { Write-Error "未知 flavor: $Flavor（支持 workbuddy|claude|generic）"; exit 1 }
  }
}

# R-10 同目录守卫（与 install.sh 对齐）：避免默认 flavor=workbuddy 把技能原地复制到源目录自身导致失败
$SrcFull = [System.IO.Path]::GetFullPath($Src)
$TgtFull = [System.IO.Path]::GetFullPath((Join-Path $Repo $Target))
if ($SrcFull.TrimEnd('\') -eq $TgtFull.TrimEnd('\')) {
  Write-Error "目标目录与源目录相同（$SrcFull），将原地复制自身导致失败。请改用 -Flavor claude/generic 或显式 -Target <其他目录>。"
  exit 1
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null
Copy-Item -Path "$Src\*" -Destination $Target -Recurse -Force
# 清理维护者工具与缓存，保持分发包干净（跨 agent 仅需技能目录）
Get-ChildItem -Path $Target -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Remove-Item -Path "$Target\build_registry.py", "$Target\REGISTRY.json" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$Target\qa-orchestrator\scripts\check_drift.py" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$Target\tools" -Recurse -Force -ErrorAction SilentlyContinue
$N = (Get-ChildItem -Path $Target -Directory).Count
Write-Host "✅ 已安装 QA skills 套件到: $Target (flavor=$Flavor)"
Write-Host "   共 $N 个技能目录（含 qa-orchestrator 编排与各阶段技能）"
Write-Host "   单技能均可独立使用；重新加载项目/agent 即可启用。"
Write-Host "   CI 门禁接入见 README「CI 门禁」章节；编排为可选层（默认不装也可逐技能调用）。"
