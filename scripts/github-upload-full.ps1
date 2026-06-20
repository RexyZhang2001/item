#Requires -Version 5.1
<#
.SYNOPSIS
  One-shot: organize all Chitung assets and push to GitHub (with Git LFS for YOLO weights).

.USAGE
  powershell -ExecutionPolicy Bypass -File "J:\China Oversea  Final\FinalAgentSuite\scripts\github-upload-full.ps1"
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = 'J:\China Oversea  Final\FinalAgentSuite',
  [string]$ParentRoot = 'J:\China Oversea  Final',
  [string]$Remote = 'https://github.com/ZTX-666/item.git',
  [string]$CommitMessage = 'Full sync: code, docs, fixtures, YOLO weights (LFS)'
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Invoke-RepoGit {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GitArgs)
  & git -c "safe.directory=$RepoRoot" -C $RepoRoot @GitArgs
}

function Copy-Tree {
  param(
    [Parameter(Mandatory)][string]$Source,
    [Parameter(Mandatory)][string]$Destination,
    [string[]]$ExcludeDirs = @()
  )
  if (-not (Test-Path $Source)) {
    Write-Warning "Skip missing: $Source"
    return
  }
  New-Item -ItemType Directory -Force -Path $Destination | Out-Null
  $xd = @('/NFL', '/NDL', '/NJH', '/NJS', '/NC', '/NS', '/NP') + ($ExcludeDirs | ForEach-Object { '/XD'; $_ })
  robocopy $Source $Destination /E /XO @xd | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "robocopy failed: $Source -> $Destination (exit $LASTEXITCODE)" }
}

function Resolve-WeightSource {
  $candidates = @(
    (Join-Path $ParentRoot 'VLM Detection\weights'),
    (Join-Path $ParentRoot 'VLMDetection\weights')
  )
  foreach ($c in $candidates) {
    $worker = Join-Path $c 'worker\yolo26x_worker.pt'
    if (Test-Path $worker) { return $c }
  }
  return $null
}

Set-Location $RepoRoot
Write-Host '==> [1/8] YOLO weights -> vlm-detection/weights/ (Git LFS)' -ForegroundColor Cyan
$weightSrc = Resolve-WeightSource
if (-not $weightSrc) { throw 'Cannot find YOLO weights under VLM Detection or VLMDetection' }

$weightDst = Join-Path $RepoRoot 'vlm-detection\weights'
foreach ($pair in @(
  @{ Sub = 'worker\yolo26x_worker.pt'; Name = 'worker/yolo26x_worker.pt' },
  @{ Sub = 'machinery\yolo26l_machinery.pt'; Name = 'machinery/yolo26l_machinery.pt' }
)) {
  $src = Join-Path $weightSrc $pair.Sub
  $dst = Join-Path $weightDst ($pair.Sub -replace '/', '\')
  if (-not (Test-Path $src)) { throw "Missing weight: $src" }
  New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
  Copy-Item $src $dst -Force
  $mb = [math]::Round((Get-Item $dst).Length / 1MB, 1)
  Write-Host "  OK $($pair.Name) (${mb} MB)"
}

Write-Host '==> [2/8] Visual test images -> fixtures/visual-samples/' -ForegroundColor Cyan
$sampleSrc = Join-Path $ParentRoot '3311 AI'
$sampleDst = Join-Path $RepoRoot 'fixtures\visual-samples'
New-Item -ItemType Directory -Force -Path $sampleDst | Out-Null
if (Test-Path $sampleSrc) {
  Copy-Tree $sampleSrc $sampleDst @()
  $jpgCount = (Get-ChildItem $sampleDst -File -Include *.jpg,*.jpeg,*.png -Recurse).Count
  Write-Host "  OK copied $jpgCount image(s)"
} else {
  Write-Warning '3311 AI folder not found — skip sample images'
}

Write-Host '==> [3/8] Product docs -> docs/product/' -ForegroundColor Cyan
$productDir = Join-Path $RepoRoot 'docs\product'
New-Item -ItemType Directory -Force -Path $productDir | Out-Null
Get-ChildItem $RepoRoot -File -Include *.md, *.html | ForEach-Object {
  Copy-Item $_.FullName (Join-Path $productDir $_.Name) -Force
}
# Redacted RTMP doc (strip API keys)
$rtmpCandidates = Get-ChildItem $RepoRoot -File -Filter 'RTMP*迁移交接*.md' -ErrorAction SilentlyContinue
foreach ($f in $rtmpCandidates) {
  $text = Get-Content $f.FullName -Raw -Encoding UTF8
  $text = $text -replace 'SECUREEYE_API_KEY=[^\r\n]+', 'SECUREEYE_API_KEY=<REDACTED-ask-project-owner>'
  $out = Join-Path $productDir ($f.BaseName + '_脱敏.md')
  Set-Content $out -Value $text -Encoding UTF8
}

Write-Host '==> [4/8] External dependencies -> external/' -ForegroundColor Cyan
$external = Join-Path $RepoRoot 'external'
Copy-Tree (Join-Path $ParentRoot '02-depth-VLM-Pipeline') (Join-Path $external '02-depth-VLM-Pipeline') @('weights', 'output', '.venv')
Copy-Tree (Join-Path $ParentRoot '03-site-memorandum-standard') (Join-Path $external 'site-memorandum-standard') @()
Copy-Tree (Join-Path $ParentRoot 'ChinaOverseas Final\docx_translate') (Join-Path $external 'docx-translate') @()
$paddleDst = Join-Path $external 'paddle-ocr-sharp'
Copy-Tree (Join-Path $ParentRoot '01-PaddleOCRSharp\PaddleOCRSharp') (Join-Path $paddleDst 'PaddleOCRSharp') @('bin', 'obj')
Copy-Tree (Join-Path $ParentRoot '01-PaddleOCRSharp\PaddlePdfOcrApp') (Join-Path $paddleDst 'PaddlePdfOcrApp') @('bin', 'obj', 'dist')

Write-Host '==> [5/8] Open-source references (slim)' -ForegroundColor Cyan
Copy-Tree (Join-Path $ParentRoot 'open-source-references') (Join-Path $RepoRoot 'open-source-references') @(
  'mlruns', 'weights', 'dist', 'node_modules', '.git', '__pycache__', '.venv'
)

Write-Host '==> [6/8] Git LFS for .pt weights' -ForegroundColor Cyan
git lfs install | Out-Null
if (-not (Test-Path (Join-Path $RepoRoot '.gitattributes'))) {
  Set-Content (Join-Path $RepoRoot '.gitattributes') "vlm-detection/weights/**/*.pt filter=lfs diff=lfs merge=lfs -text`n" -Encoding UTF8
}

Write-Host '==> [7/8] Stage all (directory-based, no Chinese pathspec)' -ForegroundColor Cyan
Invoke-RepoGit remote set-url origin $Remote
Invoke-RepoGit fetch origin main

$addPaths = @(
  '.gitignore', '.gitattributes', 'README.md', 'CODE_MAP.md',
  'agent-toolbox', 'chitung-center', 'chitung-frontend',
  'chitong-lingxun', 'docmate-shanshan', 'report-generators',
  'rtmp-tools', 'vlm-detection', 'scripts', 'safety-policy-templates-20241025',
  'whatsapp-archive', 'frontend-ui-prototype',
  'docs', 'external', 'fixtures', 'open-source-references'
)
foreach ($p in $addPaths) {
  if (Test-Path (Join-Path $RepoRoot $p)) {
    Invoke-RepoGit add -- $p
  }
}

# Block secrets / wrong docs
$blocked = Invoke-RepoGit diff --cached --name-only --diff-filter=A |
  Select-String -Pattern '(^|/)\.env$|\.env\.local$|/auth\.json$|/RTMP.*迁移交接文档_2026-06-20\.md$|/workspace/|patrol-output/|\.venv/'
if ($blocked) {
  foreach ($b in $blocked) { Invoke-RepoGit reset HEAD -- $b.ToString().Trim() }
  Write-Warning "Unstaged blocked paths: $($blocked -join ', ')"
}

$staged = @(Invoke-RepoGit diff --cached --name-only)
Write-Host "  Staged $($staged.Count) file(s)"
if ($staged.Count -eq 0) {
  Write-Host '==> Nothing new to commit.' -ForegroundColor Yellow
} else {
  Write-Host '==> [8/8] Commit & push' -ForegroundColor Cyan
  $env:GIT_AUTHOR_NAME = 'ZTX-666'
  $env:GIT_AUTHOR_EMAIL = 'ZTX-666@users.noreply.github.com'
  $env:GIT_COMMITTER_NAME = 'ZTX-666'
  $env:GIT_COMMITTER_EMAIL = 'ZTX-666@users.noreply.github.com'
  Invoke-RepoGit commit -m $CommitMessage
}

Invoke-RepoGit pull origin main --rebase
Invoke-RepoGit push origin main

Write-Host ''
Write-Host 'DONE. Verify: https://github.com/ZTX-666/item' -ForegroundColor Green
Write-Host 'Weights: vlm-detection/weights/worker/ + machinery/ (via Git LFS)' -ForegroundColor Green
Write-Host 'Handoff: docs/COLLABORATION_HANDOFF.md + docs/UPLOAD_MANIFEST.md' -ForegroundColor Green
