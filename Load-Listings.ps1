[CmdletBinding()]
param (
    [switch]$ForceRefresh,
    [string]$CustomConfigPath
)

# Set strict mode and error action preference
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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
        [switch]$IsError,
        [ValidateSet('INFO', 'WARNING', 'ERROR', 'DEBUG')]
        [string]$Level = 'INFO'
    )

    # Configurable log size limit - 1MB default
    $maxSize = 1MB
    if ((Test-Path $logFile) -and ((Get-Item $logFile).Length -gt $maxSize)) {
        $timestampTag = Get-Date -Format "yyyyMMdd_HHmmss"
        $archivedLog = Join-Path $logsDir "wmc_operations_$timestampTag.log"
        
        try {
            Rename-Item -Path $logFile -NewName $archivedLog -Force -ErrorAction Stop
            Write-LogMessage "Log file rotated to: $archivedLog" -Level DEBUG
        }
        catch {
            Write-Warning "Failed to rotate log file: $_"
        }

        # Keep only the 3 most recent rotated logs
        try {
            Get-ChildItem -Path $logsDir -Filter "wmc_operations_*.log" |
            Sort-Object LastWriteTime -Descending |
            Select-Object -Skip 2 |
            ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction Stop }
        }
        catch {
            Write-Warning "Failed to clean up old log files: $_"
        }
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp][$Level] $Message"

    switch ($Level) {
        'ERROR' { $Color = 'Red' }
        'WARNING' { $Color = 'Yellow' }
        'DEBUG' { $Color = 'Gray' }
    }

    if ($IsError) {
        $Color = 'Red'
        $Level = 'ERROR'
    }

    Write-Host $logMessage -ForegroundColor $Color

    try {
        $logMessage | Out-File -FilePath $logFile -Append -Encoding UTF8 -ErrorAction Stop
    }
    catch {
        Write-Warning "Failed to write to log file: $_"
    }
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

    $pythonExeInVenv = Join-Path $venvPath "Scripts\python.exe"

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
        & $pythonExeInVenv -m pip install -r $requirementsFile
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

# Function to safely execute file operations
function Invoke-SafeFileOperation {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Operation,
        [string]$ErrorMessage,
        [int]$RetryCount = 3,
        [int]$RetrySleepSeconds = 2
    )

    $attempt = 1
    while ($true) {
        try {
            return & $Operation
        }
        catch {
            if ($attempt -ge $RetryCount) {
                Write-LogMessage "$ErrorMessage. Final error: $_" -Level ERROR
                throw
            }
            Write-LogMessage "Attempt $attempt of $RetryCount failed: $_" -Level WARNING
            Start-Sleep -Seconds $RetrySleepSeconds
            $attempt++
        }
    }
}

# Function to validate MXF file
function Test-MxfFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    try {
        $fileInfo = Get-Item $Path
        if ($fileInfo.Length -lt 1KB) {
            Write-LogMessage "MXF file appears to be too small ($($fileInfo.Length) bytes)" -Level WARNING
            return $false
        }

        # Add basic file header validation here if needed
        return $true
    }
    catch {
        Write-LogMessage "Failed to validate MXF file: $_" -Level ERROR
        return $false
    }
}

# Run the Python script
try {
    Write-LogMessage "Running Python script to generate MXF..." -Color Yellow
    $pythonExeInVenvPath = Join-Path $venvPath "Scripts\python.exe"

    $processParams = @{
        FilePath               = $pythonExeInVenvPath
        ArgumentList           = "`"$pythonScript`""
        RedirectStandardOutput = $true
        RedirectStandardError  = $true
        UseShellExecute        = $false
        Wait                   = $true
        PassThru               = $true
        NoNewWindow            = $true
    }

    $process = Start-Process @processParams

    if ($process.ExitCode -eq 0) {
        if (Test-MxfFile -Path $mxfPath) {
            Write-LogMessage "MXF file generated and validated successfully" -Color Green

            # Backup using safe file operation
            $backupPath = Join-Path $dataDir "$timestamp-listings.mxf"
            Invoke-SafeFileOperation -Operation {
                Copy-Item -Path $mxfPath -Destination $backupPath -Force
            } -ErrorMessage "Failed to create backup file"

            # Import into WMC with validation
            Write-LogMessage "Importing MXF into Windows Media Center..." -Color Yellow
            $loadMxfResult = Start-Process -FilePath $loadMxfPath -ArgumentList "-s `"$storePath`" -i `"$mxfPath`"" -Wait -PassThru

            if ($loadMxfResult.ExitCode -eq 0) {
                Write-LogMessage "EPG data import completed successfully" -Color Green
                
                # Clean up old backups safely
                Invoke-SafeFileOperation -Operation {
                    Get-ChildItem -Path $dataDir -Filter "*-listings.mxf" |
                    Where-Object { $_.Name -ne "listings.mxf" } |
                    Sort-Object CreationTime -Descending |
                    Select-Object -Skip 2 |
                    ForEach-Object {
                        Remove-Item $_.FullName -Force
                        Write-LogMessage "Removed old backup: $($_.Name)" -Level DEBUG
                    }
                } -ErrorMessage "Failed to clean up old backups"
            }
            else {
                throw "EPG import failed with exit code: $($loadMxfResult.ExitCode)"
            }
        }
        else {
            throw "MXF file validation failed"
        }
    }
    else {
        throw "Python script failed with exit code: $($process.ExitCode)"
    }
}
catch {
    Write-LogMessage $_.Exception.Message -Level ERROR
    Write-LogMessage "Stack trace: $($_.ScriptStackTrace)" -Level DEBUG
    exit 1
}
finally {
    if ($process) {
        $process.Dispose()
    }
}

Write-LogMessage "Operation complete. Press Enter to exit..." -Color Cyan
Read-Host
