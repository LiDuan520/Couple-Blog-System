# setup_env.ps1
# 请确保保存为 UTF-8 无 BOM
$ErrorActionPreference = "Stop"

$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $projectPath "venv"

# 删除旧虚拟环境
if (Test-Path $venvPath) {
    Write-Host "删除旧虚拟环境..."
    Remove-Item -Recurse -Force $venvPath
}

# 创建新虚拟环境
Write-Host "创建新虚拟环境..."
python -m venv $venvPath

# 激活虚拟环境
Write-Host "激活虚拟环境..."
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
& $activateScript

# 升级 pip、setuptools、wheel
Write-Host "升级 pip、setuptools、wheel..."
python -m pip install --upgrade pip setuptools wheel

# 固定依赖版本
$packages = @{
    "fastapi" = "0.95.2"
    "uvicorn" = "0.23.2"
    "starlette" = "0.27.0"
    "typing-extensions" = "4.6.0"
    "anyio" = "4.12.0"
    "exceptiongroup" = "1.3.1"
    "colorama" = "0.4.6"
    "h11" = "0.16.0"
    "python-dotenv" = "1.0.0"
    "pyyaml" = "6.0.3"
    "pydantic" = "1.10.12"
}

# 安装依赖
Write-Host "安装依赖..."
foreach ($pkg in $packages.Keys) {
    $ver = $packages[$pkg]
    Write-Host "$pkg: $ver"
    python -m pip install "$pkg==$ver"
}

# 显示安装状态
Write-Host "`n依赖安装完成，版本如下："
foreach ($pkg in $packages.Keys) {
    $ver = (& python -m pip show $pkg | Select-String "Version").ToString().Split(":")[1].Trim()
    if (-not $ver) { $ver = "未安装" }
    Write-Host "$pkg: $ver"
}

# 启动 Uvicorn
Write-Host "`n启动 Uvicorn..."
Write-Host "访问 http://127.0.0.1:8000"
python -m uvicorn app.main:app --reload
