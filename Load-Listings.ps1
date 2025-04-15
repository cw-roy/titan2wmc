# Ensure we're running with admin rights
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    Exit
}

# Configuration
$pythonScript = Join-Path $PSScriptRoot "main.py"
$mxfPath = Join-Path $PSScriptRoot "data" "listings.mxf"
$loadMxfPath = "$env:SystemRoot\ehome\loadmxf.exe"
$backupPrefix = (Get-Date).ToString("yyyy-MM-dd")
$logFile = Join-Path $PSScriptRoot "data" "wmc_operations.log"
$venvPath = Join-Path $PSScriptRoot "venv"
$requirementsFile = Join-Path $PSScriptRoot "requirements.txt"

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
    Add-Content -Path $logFile -Value $logMessage
}

# Function to check Python 3 installation
function Test-Python {
    try {
        $pythonVersion = py -c "import sys; print(sys.version_info[0])"
        if ($pythonVersion -eq "3") {
            Write-LogMessage "Python 3 found" -Color Green
            return $true
        }
        Write-LogMessage "Python 3 not found (found version $pythonVersion)" -IsError
        return $false
    } catch {
        Write-LogMessage "Python not found on system" -IsError
        return $false
    }
}

# Function to setup and validate Python environment
function Initialize-VirtualEnv {
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path $venvPath)) {
        Write-LogMessage "Creating virtual environment..." -Color Yellow
        py -m venv $venvPath
        if (-not $?) {
            Write-LogMessage "Failed to create virtual environment" -IsError
            return $false
        }
    }

    # Activate virtual environment
    $activateScript = Join-Path $venvPath "Scripts" "Activate.ps1"
    if (Test-Path $activateScript) {
        . $activateScript
        Write-LogMessage "Virtual environment activated" -Color Green
    } else {
        Write-LogMessage "Virtual environment activation script not found" -IsError
        return $false
    }

    # Install/Update pip
    Write-LogMessage "Updating pip..." -Color Yellow
    py -m pip install --upgrade pip
    if (-not $?) {
        Write-LogMessage "Failed to update pip" -IsError
        return $false
    }

    # Install requirements if file exists
    if (Test-Path $requirementsFile) {
        Write-LogMessage "Installing required packages..." -Color Yellow
        pip install -r $requirementsFile
        if (-not $?) {
            Write-LogMessage "Failed to install requirements" -IsError
            return $false
        }
        Write-LogMessage "All required packages installed" -Color Green
    } else {
        Write-LogMessage "requirements.txt not found" -IsError
        return $false
    }
    
    return $true
}

# Verify WMC Installation
if (-not (Test-Path $loadMxfPath)) {
    Write-LogMessage "Windows Media Center is not installed or loadmxf.exe is missing" -IsError
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

# Launch the Python script to generate MXF
try {
    Write-LogMessage "Fetching and processing TitanTV listings..." -Color Yellow
    & "$venvPath\Scripts\python.exe" "$pythonScript"
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path $mxfPath)) {
        Write-LogMessage "MXF file generated successfully" -Color Green
        
        # Backup current MXF file with timestamp
        $backupPath = Join-Path $PSScriptRoot "data" "$backupPrefix-listings.mxf"
        Copy-Item -Path $mxfPath -Destination $backupPath -Force
        Write-LogMessage "Created backup: $backupPrefix-listings.mxf" -Color Cyan
        
        # Import the MXF file into WMC
        Write-LogMessage "Importing listings into Windows Media Center..." -Color Yellow
        $loadMxfResult = Start-Process -FilePath $loadMxfPath -ArgumentList "`"$mxfPath`"" -Wait -PassThru
        
        if ($loadMxfResult.ExitCode -eq 0) {
            Write-LogMessage "EPG data import completed successfully" -Color Green
            
            # Clean up old MXF backups (keep last 7 days)
            Get-ChildItem -Path (Join-Path $PSScriptRoot "data") -Filter "*-listings.mxf" |
                Where-Object { $_.Name -ne "listings.mxf" } |
                Sort-Object CreationTime -Descending |
                Select-Object -Skip 7 |
                ForEach-Object {
                    Remove-Item $_.FullName -Force
                    Write-LogMessage "Removed old backup: $($_.Name)" -Color Gray
                }
        } else {
            Write-LogMessage "EPG data import failed with exit code: $($loadMxfResult.ExitCode)" -IsError
        }
    } else {
        Write-LogMessage "Failed to generate MXF file" -IsError
    }
} catch {
    Write-LogMessage "Failed to execute Python script: $_" -IsError
} finally {
    # Deactivate virtual environment if it was activated
    if (Get-Command deactivate -ErrorAction SilentlyContinue) {
        deactivate
    }
}

Write-LogMessage "Operation completed. Press Enter to exit..." -Color Cyan
Read-Host