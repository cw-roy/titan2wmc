# Ensure we're running with admin rights
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    Exit
}

# Configuration
$pythonScript = Join-Path $PSScriptRoot "main.py"
$mxfPath = Join-Path $PSScriptRoot "data" "listings.mxf"
$loadMxfPath = "$env:SystemRoot\ehome\loadmxf.exe"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $PSScriptRoot "data" "wmc_operations.log"
$venvPath = Join-Path $PSScriptRoot "venv"
$requirementsFile = Join-Path $PSScriptRoot "requirements.txt"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

# Function for consistent logging
function Write-LogMessage {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        [string]$Color = "White",
        [switch]$IsError
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    
    # Console output
    if ($IsError) {
        Write-Host $Message -ForegroundColor Red
    } else {
        Write-Host $Message -ForegroundColor $Color
    }
    
    # File output
    $logMessage | Out-File -FilePath $logFile -Append -Encoding UTF8
}

# Function to check Python 3 installation
function Test-Python {
    try {
        $version = & py -c "import sys; print(sys.version_info[0])"
        if ($version -eq "3") {
            Write-LogMessage "Python 3 found" -Color Green
            return $true
        } else {
            Write-LogMessage "Python version is not 3 (found $version)" -IsError
            return $false
        }
    } catch {
        Write-LogMessage "Python not found on system" -IsError
        return $false
    }
}

# Function to setup and validate Python virtual environment
function Initialize-VirtualEnv {
    if (-not (Test-Path $venvPath)) {
        Write-LogMessage "Creating virtual environment..." -Color Yellow
        & py -m venv $venvPath
        if (-not $?) {
            Write-LogMessage "Failed to create virtual environment" -IsError
            return $false
        }
    }

    Write-LogMessage "Ensuring pip is up to date..." -Color Yellow
    & $pythonExe -m pip install --upgrade pip
    if (-not $?) {
        Write-LogMessage "Failed to upgrade pip" -IsError
        return $false
    }

    if (Test-Path $requirementsFile) {
        Write-LogMessage "Installing required packages..." -Color Yellow
        & $pythonExe -m pip install -r $requirementsFile
        if (-not $?) {
            Write-LogMessage "Failed to install required packages" -IsError
            return $false
        }
        Write-LogMessage "Required packages installed" -Color Green
    } else {
        Write-LogMessage "requirements.txt not found" -IsError
        return $false
    }

    return $true
}

# Verify WMC Installation
if (-not (Test-Path $loadMxfPath)) {
    Write-LogMessage "Windows Media Center not installed or loadmxf.exe missing" -IsError
    Exit 1
}

# Check Python and setup environment
if (-not (Test-Python)) {
    Write-LogMessage "Please install Python 3 and try again" -IsError
    Exit 1
}

if (-not (Initialize-VirtualEnv)) {
    Write-LogMessage "Failed to initialize Python environment" -IsError
    Exit 1
}

# Run the Python script
try {
    Write-LogMessage "Running Python script to generate MXF..." -Color Yellow
    & $pythonExe $pythonScript

    if ($LASTEXITCODE -eq 0 -and (Test-Path $mxfPath)) {
        Write-LogMessage "MXF file generated successfully" -Color Green

        # Backup MXF file
        $backupPath = Join-Path $PSScriptRoot "data" "$timestamp-listings.mxf"
        Copy-Item -Path $mxfPath -Destination $backupPath -Force
        Write-LogMessage "Created backup: $($backupPath | Split-Path -Leaf)" -Color Cyan

        # Import MXF into WMC
        Write-LogMessage "Importing MXF into Windows Media Center..." -Color Yellow
        $loadMxfResult = Start-Process -FilePath $loadMxfPath -ArgumentList "`"$mxfPath`"" -Wait -PassThru

        if ($loadMxfResult.ExitCode -eq 0) {
            Write-LogMessage "EPG data import completed successfully" -Color Green

            # Delete old backups (keep last 7)
            Get-ChildItem -Path (Join-Path $PSScriptRoot "data") -Filter "*-listings.mxf" |
                Where-Object { $_.Name -ne "listings.mxf" } |
                Sort-Object CreationTime -Descending |
                Select-Object -Skip 7 |
                ForEach-Object {
                    Remove-Item $_.FullName -Force
                    Write-LogMessage "Removed old backup: $($_.Name)" -Color Gray
                }
        } else {
            Write-LogMessage "EPG import failed with exit code: $($loadMxfResult.ExitCode)" -IsError
        }
    } else {
        Write-LogMessage "Python script failed or MXF file not generated" -IsError
    }
} catch {
    Write-LogMessage "Error executing Python script: $_" -IsError
}

Write-LogMessage "Operation complete. Press Enter to exit..." -Color Cyan
Read-Host
