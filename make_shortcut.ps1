# Creates a desktop shortcut with its own icon.
#
# The shortcut runs pythonw.exe launch.pyw: the report is regenerated
# and opened in the browser, without a console window.
#
#   powershell -ExecutionPolicy Bypass -File make_shortcut.ps1
#   powershell -ExecutionPolicy Bypass -File make_shortcut.ps1 -Name "My report"
#
# Keep this file in UTF-8 with BOM: Windows PowerShell 5.1 reads a file
# without a BOM in the ANSI code page and garbles any non-ASCII text.

param([string]$Name = 'ActivityWatch Report')

$ErrorActionPreference = 'Stop'

$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $base 'launch.pyw'
$icon = Join-Path $base 'dashboard.ico'

if (-not (Test-Path $launcher)) { throw "launch.pyw not found in $base" }
if (-not (Test-Path $icon)) { throw "dashboard.ico not found - run first: python make_icon.py" }

# Take the real pythonw.exe next to python.exe. The WindowsApps alias does
# not work for shortcuts: it is a reparse point and IconLocation breaks.
$pythonExe = & python -c "import sys; print(sys.executable)"
$pythonw = Join-Path (Split-Path -Parent $pythonExe) 'pythonw.exe'
if (-not (Test-Path $pythonw)) { $pythonw = $pythonExe }

$desktop = [Environment]::GetFolderPath('Desktop')
$path = Join-Path $desktop "$Name.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($path)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = '"{0}"' -f $launcher
$shortcut.WorkingDirectory = $base
$shortcut.IconLocation = "$icon,0"
$shortcut.Description = 'Regenerate the ActivityWatch report and open it'
$shortcut.WindowStyle = 1
$shortcut.Save()

Write-Output "Shortcut: $path"
Write-Output "  runs:   $pythonw"
Write-Output "  script: $launcher"
Write-Output "  icon:   $icon"
