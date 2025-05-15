# Requires -Version 3.0
# Load-Listings.ps1

# Ensure admin rights elevation
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    Exit
}

# Set the script to run in local directory
Set-Location -Path $PSScriptRoot

# Function for consistent logging
function Write-LogMessage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        [string]$Color = "White",
        [switch]$IsError
    )

    # Rotate log file if it exceeds 1MB
    $maxSize = 1MB
    if ((Test-Path $logFile) -and ((Get-Item $logFile).Length -gt $maxSize)) {
        $timestampTag = Get-Date -Format "yyyyMMdd_HHmmss"
        $archivedLog = Join-Path $logsDir "wmc_operations_$timestampTag.log"
        Rename-Item -Path $logFile -NewName $archivedLog -Force

        # Keep only the 3 most recent rotated logs
        Get-ChildItem -Path $logsDir -Filter "wmc_operations_*.log" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -Skip 2 |
        ForEach-Object { Remove-Item $_.FullName -Force }
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"

    if ($IsError) {
        Write-Host $logMessage -ForegroundColor Red
    }
    else {
        Write-Host $logMessage -ForegroundColor $Color
    }

    $logMessage | Out-File -FilePath $logFile -Append -Encoding UTF8
}

# Configuration
$pythonScript = Join-Path $PSScriptRoot "main.py"
$dataDir = Join-Path $PSScriptRoot "data"
$logsDir = Join-Path $PSScriptRoot "logs"
$mxfPath = Join-Path $dataDir "listings.mxf"
$logFile = Join-Path $logsDir "wmc_operations.log"
$venvPath = Join-Path $PSScriptRoot "venv"
$requirementsFile = Join-Path $PSScriptRoot "requirements.txt"
$pythonExe = "python"
$loadMxfPath = "$env:SystemRoot\ehome\loadmxf.exe"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$epgPath = "C:\ProgramData\Microsoft\eHome"

# Ensure 'data' and 'logs' directories exist
foreach ($dir in @($dataDir, $logsDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-LogMessage "Created directory: $dir" -Color DarkGray
    }
}

# Function to check Python 3 installation
function Test-Python {
    try {
        $version = & $pythonExe --version 2>&1
        if ($version -match "^Python 3") {
            Write-LogMessage "Python 3 found via '$pythonExe'" -Color Green
            return $true
        }
        else {
            Write-LogMessage "Python version is not 3: $version" -IsError
            return $false
        }
    }
    catch {
        Write-LogMessage "Python not found on system using '$pythonExe'" -IsError
        return $false
    }
}

# Setup and validate virtual environment

function Initialize-VirtualEnv {
    # Create venv if it doesn't exist
    if (-not (Test-Path $venvPath)) {
        Write-LogMessage "Creating virtual environment..." -Color Yellow
        & $pythonExe -m venv $venvPath
        if (-not $?) {
            Write-LogMessage "Failed to create virtual environment" -IsError
            return $false
        }
    }

    # Initialize $startInfo properly
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $pythonExeInVenv = Join-Path $venvPath "Scripts\python.exe"
    $startInfo.FileName = $pythonExeInVenv

    # Activate is implied by calling python in the venv
    Write-LogMessage "Checking required packages..." -Color Yellow

    if (-not (Test-Path $requirementsFile)) {
        Write-LogMessage "requirements.txt not found" -IsError
        return $false
    }

    # Get installed packages
    $installed = & $pythonExeInVenv -m pip freeze | ForEach-Object { ($_ -split '==')[0].ToLower() }
    $required = Get-Content $requirementsFile | Where-Object { $_ -match '\S' -and $_ -notmatch '^\s*#' } |
    ForEach-Object { ($_ -split '==')[0].ToLower() }

    # Determine missing packages
    $missing = $required | Where-Object { $_ -notin $installed }

    if ($missing.Count -gt 0) {
        Write-LogMessage "Installing missing packages: $($missing -join ', ')" -Color Yellow
        & $pythonExeInVenv -m pip install -r $requirementsFile --disable-pip-version-check --quiet
        if (-not $?) {
            Write-LogMessage "Failed to install required packages" -IsError
            return $false
        }
        Write-LogMessage "Missing packages installed" -Color Green
    }
    else {
        Write-LogMessage "All required packages are already installed" -Color Green
    }

    return $true
}


# Get active EPG store path
function Get-ActiveStorePath {
    $epgRegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Media Center\Service\Epg"

    try {
        $currentDB = Get-ItemPropertyValue -Path $epgRegPath -Name "CurrentDatabase" -ErrorAction Stop
        if ($currentDB -and (Test-Path $currentDB)) {
            Write-LogMessage "Found CurrentDatabase in registry: $currentDB" -Color Cyan
            return $currentDB
        }
    }
    catch {
        Write-LogMessage "Registry entry 'CurrentDatabase' not found. Falling back to auto-detection." -Color Yellow
    }

    # Fallback: find most recent matching .db and folder pair
    $dbFiles = Get-ChildItem -Path $epgPath -Filter "mcepg*.db" -File
    $validStores = @()

    foreach ($file in $dbFiles) {
        $folderName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $folderPath = Join-Path $epgPath $folderName
        if (Test-Path $folderPath) {
            $validStores += [PSCustomObject]@{
                Path     = $file.FullName
                Modified = $file.LastWriteTime
            }
        }
    }

    if ($validStores.Count -eq 0) {
        Write-LogMessage "No valid store database files found in $epgPath" -IsError
        return $null
    }

    $mostRecent = $validStores | Sort-Object Modified -Descending | Select-Object -First 1
    Write-LogMessage "Using most recently modified store: $($mostRecent.Path)" -Color Cyan
    return $mostRecent.Path
}

# Verify WMC is installed
if (-not (Test-Path $loadMxfPath)) {
    Write-LogMessage "Windows Media Center not installed or loadmxf.exe missing" -IsError
    Exit 1
}

# Setup Python environment
if (-not (Test-Python)) {
    Write-LogMessage "Please install Python 3 and try again" -IsError
    Read-Host "Press Enter to exit..."
    Exit 1
}

if (-not (Initialize-VirtualEnv)) {
    Write-LogMessage "Failed to initialize Python environment" -IsError
    Read-Host "Press Enter to exit..."
    Exit 1
}

# Determine store path
$storePath = Get-ActiveStorePath
if (-not $storePath) {
    Write-LogMessage "Unable to determine active WMC store database path." -IsError
    Read-Host "Press Enter to exit..."
    Exit 1
}

# Run the Python script

try {
    Write-LogMessage "Running Python script to generate MXF..." -Color Yellow

    # Initialize $startInfo
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $pythonExeInVenvPath = Join-Path $venvPath "Scripts\python.exe"
    $startInfo.FileName = $pythonExeInVenvPath
    $startInfo.Arguments = "`"$pythonScript`""
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.WorkingDirectory = $PSScriptRoot

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo

    $null = $process.Start()
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    if ($stdout) {
        Write-LogMessage "Python stdout:`n$stdout" -Color Gray
    }
    if ($stderr) {
        Write-LogMessage "Python stderr:`n$stderr" -Color DarkYellow
    }

    if ($process.ExitCode -eq 0 -and (Test-Path $mxfPath)) {
        Write-LogMessage "MXF file generated successfully" -Color Green
    }
    else {
        Write-LogMessage "Python script failed with exit code: $($process.ExitCode)" -IsError
    }
}
catch {
    Write-LogMessage "An error occurred while running the Python script: $_" -IsError
}

# try {
#     Write-LogMessage "Running Python script to generate MXF..." -Color Yellow
#     $pythonExeInVenvPath = Join-Path $venvPath "Scripts\python.exe"
#     $startInfo.FileName = $pythonExeInVenvPath
#     $startInfo.Arguments = "`"$pythonScript`""
#     $startInfo.RedirectStandardOutput = $true
#     $startInfo.RedirectStandardError = $true
#     $startInfo.UseShellExecute = $false
#     $startInfo.CreateNoWindow = $true
#     $startInfo.WorkingDirectory = $PSScriptRoot

#     $process = New-Object System.Diagnostics.Process
#     $process.StartInfo = $startInfo

#     $null = $process.Start()
#     $stdout = $process.StandardOutput.ReadToEnd()
#     $stderr = $process.StandardError.ReadToEnd()
#     $process.WaitForExit()

#     if ($stdout) {
#         Write-LogMessage "Python stdout:`n$stdout" -Color Gray
#     }
#     if ($stderr) {
#         Write-LogMessage "Python stderr:`n$stderr" -Color DarkYellow
#     }

#     if ($process.ExitCode -eq 0 -and (Test-Path $mxfPath)) {
#         Write-LogMessage "MXF file generated successfully" -Color Green
#     }
#     else {
#         Write-LogMessage "Python script failed with exit code: $($process.ExitCode)" -IsError
#     }
# }
# catch {
#     Write-LogMessage "An error occurred while running the Python script: $_" -IsError
# }

# Import into WMC
Write-LogMessage "Importing MXF into Windows Media Center..." -Color Yellow
$loadMxfResult = Start-Process -FilePath $loadMxfPath -ArgumentList "-s `"$storePath`" -i `"$mxfPath`"" -Wait -PassThru

if ($loadMxfResult.ExitCode -eq 0) {
    Write-LogMessage "EPG data import completed successfully" -Color Green

    # Clean up old backups
    Get-ChildItem -Path $dataDir -Filter "*-listings.mxf" |
    Where-Object { $_.Name -ne "listings.mxf" } |
    Sort-Object CreationTime -Descending |
    Select-Object -Skip 2 |
    ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-LogMessage "Removed old backup: $($_.Name)" -Color Gray
    }
}
else {
    Write-LogMessage "EPG import failed with exit code: $($loadMxfResult.ExitCode)" -IsError
}

Write-LogMessage "Finalizing the operation..." -Color Cyan

Write-LogMessage "Operation complete. Press Enter to exit..." -Color Cyan
Read-Host