# RadiKal Silent Startup with Loading Window
# Runs backend and frontend without terminal windows

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create loading form
$form = New-Object System.Windows.Forms.Form
$form.Text = "RadiKal Startup"
$form.Size = New-Object System.Drawing.Size(400, 220)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)

# Icon/Logo Label
$logoLabel = New-Object System.Windows.Forms.Label
$logoLabel.Text = "RadiKal"
$logoLabel.Font = New-Object System.Drawing.Font("Segoe UI", 24, [System.Drawing.FontStyle]::Bold)
$logoLabel.ForeColor = [System.Drawing.Color]::FromArgb(59, 130, 246)
$logoLabel.AutoSize = $true
$logoLabel.Location = New-Object System.Drawing.Point(130, 20)
$form.Controls.Add($logoLabel)

# Title Label
$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "Starting Services..."
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Regular)
$titleLabel.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$titleLabel.AutoSize = $true
$titleLabel.Location = New-Object System.Drawing.Point(120, 60)
$form.Controls.Add($titleLabel)

# Status Label
$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = "Initializing..."
$statusLabel.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$statusLabel.AutoSize = $false
$statusLabel.Size = New-Object System.Drawing.Size(360, 25)
$statusLabel.Location = New-Object System.Drawing.Point(20, 100)
$statusLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$form.Controls.Add($statusLabel)

# Progress Bar
$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(50, 135)
$progressBar.Size = New-Object System.Drawing.Size(300, 20)
$progressBar.Style = "Continuous"
$progressBar.Maximum = 100
$progressBar.Value = 0
$form.Controls.Add($progressBar)

# Info Label
$infoLabel = New-Object System.Windows.Forms.Label
$infoLabel.Text = "Please wait while services start..."
$infoLabel.Font = New-Object System.Drawing.Font("Segoe UI", 8)
$infoLabel.ForeColor = [System.Drawing.Color]::FromArgb(100, 116, 139)
$infoLabel.AutoSize = $false
$infoLabel.Size = New-Object System.Drawing.Size(360, 20)
$infoLabel.Location = New-Object System.Drawing.Point(20, 165)
$infoLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$form.Controls.Add($infoLabel)

# Timer for startup process
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 500
$script:step = 0

$timer.Add_Tick({
    $script:step++
    
    switch($script:step) {
        1 {
            $statusLabel.Text = "Starting Backend Server..."
            $progressBar.Value = 10
            
            # Start Backend
            $backendPath = Join-Path $PSScriptRoot "backend"
            Start-Process -FilePath "python" -ArgumentList "main.py" -WorkingDirectory $backendPath -WindowStyle Hidden
        }
        4 {
            $statusLabel.Text = "Backend initializing..."
            $progressBar.Value = 30
        }
        8 {
            $statusLabel.Text = "Backend ready"
            $progressBar.Value = 50
        }
        10 {
            $statusLabel.Text = "Starting Frontend Server..."
            $progressBar.Value = 60
            
            # Start Frontend
            $frontendPath = Join-Path $PSScriptRoot "frontend"
            Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory $frontendPath -WindowStyle Hidden
        }
        14 {
            $statusLabel.Text = "Frontend initializing..."
            $progressBar.Value = 80
        }
        18 {
            $statusLabel.Text = "Opening browser..."
            $progressBar.Value = 95
            
            # Open browser
            Start-Process "http://localhost:3000"
        }
        20 {
            $statusLabel.Text = "RadiKal is ready!"
            $progressBar.Value = 100
            $infoLabel.Text = "Services running at localhost:3000 and localhost:8000"
        }
        24 {
            $timer.Stop()
            $form.Close()
        }
    }
})

# Start timer and show form
$timer.Start()
$form.Add_Shown({$form.Activate()})
[void]$form.ShowDialog()

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RadiKal is Running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services:" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "To stop services:" -ForegroundColor Yellow
Write-Host "  Run: .\STOP_ALL.ps1" -ForegroundColor White
Write-Host "  Or use Task Manager to end 'python.exe' and 'node.exe'" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
