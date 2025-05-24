# titan2wmc

A tool to fetch TV listings from TitanTV and import them into Windows Media Center (WMC).

- Warning - this is very much a work in progress. Check the commit comments, I'll try to commit with notes saying whether I've broken it trying to tweak it up.

05/24/2025: This seems to be working pretty well. For now, it looks like it's putting the right files in the right places. No testing has been done on a physical machine with a tuner card installed - see notes below. I've verified the MXF file structure according to what MS says it should look like so it should work, but YMMV. More info in Resources section.

## The death of Zap2it TV listings

#### The Zap2it TV listings site was taken down sometime in late March 2025

- Cord Cutters article [here](https://cordcuttersnews.com/the-popular-online-tv-guide-service-zap2it-tv-shuts-down-is-replaced-by-newsnation/) or [here](https://web.archive.org/web/20250000000000*/https://cordcuttersnews.com/the-popular-online-tv-guide-service-zap2it-tv-shuts-down-is-replaced-by-newsnation/)
- This made the tools I was using ([ZAP2XML](https://web.archive.org/web/20200426004001/zap2xml.awardspace.info/) and [EPG Collector](https://sourceforge.net/projects/epgcollector/)) obsolete
- I needed an alternative so I figured I'd give it a shot using my favorite languages.
  - Python for API interaction and data massaging
  - PowerShell for Windows file manipulation
- I chose [TitanTV](https://titantv.com/) as my listings provider replacement

## Description

This tool automates the process of:

1. Fetching TV program listings from TitanTV's API
2. Converting the data into WMC's MXF format
3. Importing the listings into Windows Media Center

## Resources

- [Itechtics article on obtaining Windows Media Center](https://web.archive.org/web/20250000000000*/https://www.itechtics.com/windows-media-center/)
  - [Download](https://mega.nz/file/OLBTSJRB#s_GEqA_SXciRh80woQlMPylSSsCwsNUAOkkYCGyG25I)
- Howtogeek article: [How to Install Windows Media Center on Windows 10](https://www.howtogeek.com/258695/how-to-install-windows-media-center-on-windows-10/)
- [The Green Button forum](https://www.thegreenbutton.tv/forums/)

- Microsoft links:
  - [Windows Media Center Guide Listings Format | Microsoft Learn](<https://learn.microsoft.com/en-us/previous-versions/windows/desktop/windows-media-center-sdk-technical-articles/dd776338(v=msdn.10)#contents>)
  - [Windows Media Center Software Development Kit | Microsoft Learn](<https://learn.microsoft.com/en-us/previous-versions/msdn10/bb895967(v=msdn.10)>)
- I'll post more here as I find them, this is still a work in progress

## NOTE: this has only been tested on Win10 and Win11 in VirtualBox.

- Download VirtualBox [here](https://www.virtualbox.org/).
- No guarantees it will work on older versions of Windows, but it should...I think.

### Testing still to be done on a physical machine.

- Because I've only used this on a VM, I haven't been able to attach a TV tuner card.
  Therefore, I can't do a channel scan and WMC doesn't actually show the listings grid.
  I'll have to test on a physical machine when I get a chance.

## Requirements

- Windows 8.1 or later with
- Windows Media Center installed
- Python 3.x
- PowerShell 3.0 or later
- Administrator privileges (required for WMC integration)
- Active internet connection

## Setup

I won't post the APIs here but you should be able to figure them out by running a HAR capture while visiting TitanTV's site. HAR files can be huge and hard to search. Modern text editors add so much overhead that it makes it extremely slow, so I used vi. You can use vi to search for APIs like this:

```
:vimgrep /https:\/\/titantv\.com\/api\/\w\+\// %
```

Create a `.env` file in the root directory with your TitanTV credentials:

```
TITANTV_USER_ID=[Unique to username, obtain this from API 'documentation']
TITANTV_LINEUP_ID=[Unique to your lineup set in TitanTV's website preferences]
TITANTV_USERNAME=[your_username]
TITANTV_PASSWORD=[your_password]
```

## Usage

### Creating a Desktop Shortcut to Load-Listings.ps1

1. Create a Shortcut Manually
2. Right-click your desktop and select "New" → "Shortcut"
3. For the location, enter the following (adjust the path as needed):

- `powershell.exe -ExecutionPolicy Bypass -NoProfile -File "C:\Path\To\Load-Listings.ps1"`

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
