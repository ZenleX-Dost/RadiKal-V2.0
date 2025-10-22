# START_RADIKAL.bat - Fixed Version

## What It Does

1. Launches START_SILENT.ps1 PowerShell script
2. Shows a loading window with progress bar
3. Starts Backend (Python) in background
4. Starts Frontend (Node.js) in background
5. Opens browser automatically
6. No terminal windows!

## Usage

Simply double-click `START_RADIKAL.bat`

## Loading Window Features

- Dark theme UI (matches RadiKal)
- Progress bar (0% to 100%)
- Status messages:
  - "Starting Backend Server..."
  - "Backend initializing..."
  - "Backend ready"
  - "Starting Frontend Server..."
  - "Frontend initializing..."
  - "Opening browser..."
  - "RadiKal is ready!"
- Auto-closes after ~12 seconds

## Troubleshooting

### "Script cannot be loaded" error
Run this once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Nothing happens
1. Make sure Python is installed: `python --version`
2. Make sure Node.js is installed: `node --version`
3. Check if ports 3000 and 8000 are free

### Services don't start
Run `STOP_ALL.ps1` first to kill any existing processes, then try again.

### Want to see logs?
Use `START_ALL.bat` instead for development mode with visible terminals.

## Technical Details

The .bat file calls PowerShell with `-ExecutionPolicy Bypass` to avoid execution policy issues.
The PowerShell script creates a Windows Forms GUI with:
- System.Windows.Forms for the window
- System.Drawing for colors and fonts
- Timer for progress updates
- Hidden process windows for Python and Node

## Files Involved

- `START_RADIKAL.bat` - Batch launcher
- `START_SILENT.ps1` - PowerShell script with GUI
- `backend/main.py` - Backend server
- `frontend/package.json` - Frontend config (npm run dev)
