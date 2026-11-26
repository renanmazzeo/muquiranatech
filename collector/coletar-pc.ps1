# MuquiranaTech: coleta da Amazon feita pelo PC do dono (a Amazon bloqueia o robô do GitHub).
#
# Roda numa cópia própria do repositório em %LOCALAPPDATA%\MuquiranaTech\repo, nunca na pasta de trabalho,
# porque faz "git reset --hard" para sempre partir da versão mais nova do GitHub.
# O Agendador de Tarefas do Windows chama este script a cada 3 horas (tarefa "MuquiranaTech - Amazon").
#
#   Instalar ou reinstalar:  powershell -ExecutionPolicy Bypass -File collector\coletar-pc.ps1 -Instalar
#   Rodar agora, na mão:     powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\MuquiranaTech\repo\collector\coletar-pc.ps1"
#   Ver o log:               notepad "$env:LOCALAPPDATA\MuquiranaTech\coleta.log"
param([switch]$Instalar, [string]$Lojas = "amazon")

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$Home_ = Join-Path $env:LOCALAPPDATA "MuquiranaTech"
$Repo = Join-Path $Home_ "repo"
$Log = Join-Path $Home_ "coleta.log"
$Url = "https://github.com/renanmazzeo/muquiranatech.git"
$Tarefa = "MuquiranaTech - Amazon"
New-Item -ItemType Directory -Force $Home_ | Out-Null

function Write-Log($msg) {
    $linha = "{0:yyyy-MM-dd HH:mm:ss}  {1}" -f (Get-Date), $msg
    Add-Content -Path $Log -Value $linha -Encoding utf8
    Write-Output $linha
}

function Invoke-Git {
    # avisos do git vão para stderr; no PowerShell 5.1 isso viraria erro com "Stop"
    $ErrorActionPreference = "Continue"
    $out = & git -C $Repo @args 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') falhou: $out" }
    $out
}

function Invoke-Py {
    $ErrorActionPreference = "Continue"
    & $py @args 2>&1 | ForEach-Object { "$_" }
}

if ($Instalar) {
    if (-not (Test-Path (Join-Path $Repo ".git"))) {
        git clone -q $Url $Repo
        if ($LASTEXITCODE -ne 0) { throw "git clone falhou" }
    }
    if (-not (Test-Path (Join-Path $Repo ".venv"))) {
        python -m venv (Join-Path $Repo ".venv")
        & (Join-Path $Repo ".venv\Scripts\pip.exe") install -q -r (Join-Path $Repo "collector\requirements.txt")
    }
    git -C $Repo config user.name "muquirana-pc"
    git -C $Repo config user.email "muquiranatech@users.noreply.github.com"
    git -C $Repo config core.autocrlf false
    $script = Join-Path $Repo "collector\coletar-pc.ps1"
    $acao = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`""
    # a cada 3h, começando 1h30 depois do robô do GitHub (que roda em 0h, 3h, 6h... de Brasília)
    $gatilho = New-ScheduledTaskTrigger -Once -At (Get-Date "01:30") `
        -RepetitionInterval (New-TimeSpan -Hours 3) -RepetitionDuration (New-TimeSpan -Days 3650)
    $config = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 45) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $Tarefa -Action $acao -Trigger $gatilho -Settings $config `
        -Description "Coleta os preços da Amazon para o MuquiranaTech e envia ao GitHub." -Force | Out-Null
    Write-Log "Instalado: tarefa '$Tarefa' a cada 3h (repo em $Repo)"
    return
}

try {
    $py = Join-Path $Repo ".venv\Scripts\python.exe"
    $muq = Join-Path $Repo "collector\muq.py"
    $copia = Join-Path $Home_ "coleta.db"
    Write-Log "Início da coleta: $Lojas"
    Invoke-Git fetch -q origin main | Out-Null
    Invoke-Git reset -q --hard origin/main | Out-Null
    Copy-Item (Join-Path $Repo "data\muquirana.db") $copia -Force
    $env:MUQ_DB = $copia
    $saida = Invoke-Py $muq coletar --lojas $Lojas
    Remove-Item Env:MUQ_DB
    $saida | Where-Object { $_ -match "^==|!" } | ForEach-Object { Write-Log $_ }

    for ($i = 1; $i -le 5; $i++) {
        # parte da versão mais nova do GitHub e mescla só os preços desta coleta
        Invoke-Git fetch -q origin main | Out-Null
        Invoke-Git reset -q --hard origin/main | Out-Null
        Invoke-Py $muq mesclar $copia --lojas $Lojas | ForEach-Object { Write-Log $_ }
        Invoke-Py $muq exportar | ForEach-Object { Write-Log $_ }
        Invoke-Git add data/muquirana.db data.js | Out-Null
        $ErrorActionPreference = "Continue"
        & git -C $Repo diff --cached --quiet
        $semMudanca = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = "Stop"
        if ($semMudanca) { Write-Log "Nada novo para enviar."; break }
        $quando = Get-Date -Format "yyyy-MM-dd HH'h'mm"
        Invoke-Git commit -q -m "Preços de $quando · Amazon (PC)" | Out-Null
        $ErrorActionPreference = "Continue"
        & git -C $Repo push -q 2>&1 | Out-Null
        $ok = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = "Stop"
        if ($ok) { Write-Log "Enviado ao GitHub."; break }
        Write-Log "Push recusado (tentativa $i); tentando de novo."
        Start-Sleep -Seconds 20
    }
}
catch {
    Write-Log "ERRO: $_"
    exit 1
}
finally {
    # o log não cresce para sempre: guarda as últimas 2000 linhas
    if ((Test-Path $Log) -and ((Get-Content $Log).Count -gt 2000)) {
        (Get-Content $Log -Tail 2000) | Set-Content $Log -Encoding utf8
    }
}
