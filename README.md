# titan2wmc

A tool to fetch TV listings from TitanTV and import them into Windows Media Center (WMC).

## Description

This tool automates the process of:
1. Fetching TV program listings from TitanTV's API
2. Converting the data into WMC's MXF format
3. Importing the listings into Windows Media Center

## Requirements

- Windows 8.1 or later with Windows Media Center installed
- Python 3.x 
- PowerShell 3.0 or later
- Administrator privileges (required for WMC integration)
- Active internet connection

## Setup

Create a `.env` file in the root directory with your TitanTV credentials:
```
TITANTV_USERNAME=your_username
TITANTV_PASSWORD=your_password
```

## Usage

### Creating a Desktop Shortcut to Load-Listings.ps1

1. Create a Shortcut Manually
2. Right-click your desktop and select "New" → "Shortcut"
3. For the location, enter the following (adjust the path as needed):
- ```powershell.exe -ExecutionPolicy Bypass -NoProfile -File "C:\Path\To\Load-Listings.ps1"```
4. Click "Next", give the shortcut a name like "Load TV Listings`"
5. Click "Finish"

### Set the Shortcut to Run as Administrator

1. Right-click the shortcut and choose "Properties"
2. Go to the "Shortcut" tab and click the "Advanced..." button
3. Check the box for "Run as administrator" and click OK, then Apply

The script will:
   - Check for required components
   - Set up Python environment
   - Fetch latest listings
   - Generate MXF file
   - Import listings into WMC
   - Maintain backups of previous listings

## Important Notes

- This tool is for personal use only
- No warranty or liability is assumed for any issues that may arise from using this tool
- The tool creates backups of MXF files in the `data` directory
- Logs are stored in the `logs` directory
- Previous listings are retained for 7 days before automatic cleanup

## Troubleshooting

Check the following logs for issues:
- `logs/titantv.log` - API and data processing logs
- `logs/wmc_operations.log` - WMC import operation logs

## Technical Details

The project uses:
- PowerShell for Windows/WMC integration
- Python for API interaction and data processing
- Virtual environment for dependency management
- UTC timestamps for consistency