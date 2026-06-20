# Batch 2: copy external assets + stage docs, then commit & push.
# Run from: J:\China Oversea  Final\FinalAgentSuite

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$Parent = Split-Path -Parent $Root
Set-Location $Root

Write-Host "==> Preparing docs/product ..."
$product = Join-Path $Root 'docs\product'
New-Item -ItemType Directory -Force -Path $product | Out-Null

$docNames = @(
  '飞书机器人五阶段实施工具清单.md',
  '赤瞳安全智能平台_产品介绍_v2.md',
  '赤瞳安全智能平台_产品技术方案.md',
  '赤瞳安全智能平台_完成度差距与开发路线_2026-06-20.md',
  '赤瞳守护者_RTMP+YOLO+VLM_实施指引.md',
  '赤瞳守护者_零上下文接手开发手册.md',
  '耀耀慧读_赤瞳中台对接交接文档.md',
  '耀耀慧读结构化输入接入实施指令.md',
  'PaddleOCRSharp项目代码深度解析.md',
  '萤石云RTMP取流问题诊断与解决方案.md',
  'CHITONGLINGXUN_MIGRATION_RUNBOOK.md',
  'PRODUCT_HANDOFF.md',
  'FINAL_VERSIONS.md',
  'CORE_CODE_MIGRATION_2026-06-17.md',
  'CODE_RELATIONSHIP_GRAPH.md',
  'CODE_RELATIONSHIP_GRAPH_2026-06-20.md',
  'CODE_ARCHITECTURE_SEARCH_INDEX.md'
)
foreach ($name in $docNames) {
  $src = Join-Path $Root $name
  if (Test-Path $src) { Copy-Item $src (Join-Path $product $name) -Force }
}

$htmlNames = @(
  '赤瞳安全智能平台_技术架构图.html',
  '赤瞳4加1地盘管理功能地图.html',
  '赤瞳Skill技能全景.html',
  '赤瞳多智能体工作流全景.html',
  '赤瞳视觉自适应巡检闭环_演示.html',
  'chitung_function_map.html'
)
foreach ($name in $htmlNames) {
  $src = Join-Path $Root $name
  if (Test-Path $src) { Copy-Item $src (Join-Path $product $name) -Force }
}

# Redacted RTMP handoff (strip real API key)
$rtmpSrc = Join-Path $Root 'RTMP赤瞳守护者_迁移交接文档_2026-06-20.md'
if (Test-Path $rtmpSrc) {
  $text = Get-Content $rtmpSrc -Raw -Encoding UTF8
  $text = $text -replace 'SECUREEYE_API_KEY=[^\r\n]+', 'SECUREEYE_API_KEY=<REDACTED-ask-project-owner>'
  Set-Content (Join-Path $product 'RTMP赤瞳守护者_迁移交接文档_2026-06-20_脱敏.md') -Value $text -Encoding UTF8
}

Write-Host "==> Copying external dependencies ..."
$external = Join-Path $Root 'external'
New-Item -ItemType Directory -Force -Path $external | Out-Null

function Copy-Tree($src, $dst, [string[]]$excludeDirs) {
  if (-not (Test-Path $src)) { Write-Warning "Skip missing: $src"; return }
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  $xd = @('/NFL','/NDL','/NJH','/NJS','/NC','/NS','/NP') + ($excludeDirs | ForEach-Object { "/XD"; $_ })
  robocopy $src $dst /E /XO @xd | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "robocopy failed: $src -> $dst" }
}

Copy-Tree (Join-Path $Parent '02-depth-VLM-Pipeline') (Join-Path $external '02-depth-VLM-Pipeline') @('weights','output','.venv')
Copy-Tree (Join-Path $Parent '03-site-memorandum-standard') (Join-Path $external 'site-memorandum-standard') @()
Copy-Tree (Join-Path $Parent 'ChinaOverseas Final\docx_translate') (Join-Path $external 'docx-translate') @()

$paddleDst = Join-Path $external 'paddle-ocr-sharp'
New-Item -ItemType Directory -Force -Path $paddleDst | Out-Null
Copy-Tree (Join-Path $Parent '01-PaddleOCRSharp\PaddleOCRSharp') (Join-Path $paddleDst 'PaddleOCRSharp') @('bin','obj')
Copy-Tree (Join-Path $Parent '01-PaddleOCRSharp\PaddlePdfOcrApp') (Join-Path $paddleDst 'PaddlePdfOcrApp') @('bin','obj','dist')

Write-Host "==> Copying open-source-references (excluding heavy dirs) ..."
$ossSrc = Join-Path $Parent 'open-source-references'
$ossDst = Join-Path $Root 'open-source-references'
Copy-Tree $ossSrc $ossDst @('mlruns','weights','dist','node_modules','.git','__pycache__','.venv')

function Invoke-RepoGit {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GitArgs)
  & git -c "safe.directory=$Root" @GitArgs
}

# Use directory adds only — avoid Chinese filenames in git CLI (PowerShell encoding bug)
Invoke-RepoGit add .gitignore docs fixtures external open-source-references `
  whatsapp-archive frontend-ui-prototype scripts/github-upload-batch2.ps1
Get-ChildItem -Path $Root -File -Filter '*.md' | ForEach-Object { Invoke-RepoGit add -- $_.FullName }

# Verify no secrets staged
$bad = Invoke-RepoGit diff --cached --name-only | Select-String -Pattern '\.env$|\.pt$|auth\.json|RTMP赤瞳守护者_迁移交接文档_2026-06-20\.md$'
if ($bad) { throw "Blocked sensitive files: $bad" }

Invoke-RepoGit fetch origin main

$env:GIT_AUTHOR_NAME = 'ZTX-666'
$env:GIT_AUTHOR_EMAIL = 'ZTX-666@users.noreply.github.com'
$env:GIT_COMMITTER_NAME = 'ZTX-666'
$env:GIT_COMMITTER_EMAIL = 'ZTX-666@users.noreply.github.com'

$staged = @(Invoke-RepoGit diff --cached --name-only)
if ($staged.Count -eq 0) {
  Write-Host "==> Nothing new to commit. Remote may already be up to date."
} else {
  Invoke-RepoGit commit -m "Add batch2: docs, WhatsApp archive, UI prototype, external OCR/depth refs"
}

Invoke-RepoGit push origin main

Write-Host "==> Done. Verify: https://github.com/ZTX-666/item"
