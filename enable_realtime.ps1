# PowerShell script to enable real-time processing mode

Write-Host "🎥 Enabling Real-Time Processing Mode..." -ForegroundColor Cyan
Write-Host ""

# Backup current files
Write-Host "📦 Creating backups..." -ForegroundColor Yellow
Copy-Item "frontend\app.py" "frontend\app_backup.py" -Force
Copy-Item "master_worker\master_worker.py" "master_worker\master_worker_backup.py" -Force
Write-Host "✅ Backups created" -ForegroundColor Green
Write-Host ""

# Switch to real-time versions
Write-Host "🔄 Switching to real-time versions..." -ForegroundColor Yellow
Copy-Item "frontend\app_realtime.py" "frontend\app.py" -Force
Copy-Item "master_worker\master_worker_realtime.py" "master_worker\master_worker.py" -Force
Write-Host "✅ Files updated" -ForegroundColor Green
Write-Host ""

# Restart services
Write-Host "🔄 Restarting services..." -ForegroundColor Yellow
docker-compose restart streamlit_ui api_server master_worker

Write-Host ""
Write-Host "✅ Real-Time Mode Enabled!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access the real-time UI at: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 What's new:" -ForegroundColor White
Write-Host "  • Live frame-by-frame processing view" -ForegroundColor White
Write-Host "  • Real-time statistics updates" -ForegroundColor White
Write-Host "  • Progress bar with percentage" -ForegroundColor White
Write-Host "  • Watch AI analyze each frame" -ForegroundColor White
Write-Host ""
Write-Host "💡 To revert to standard mode, run: .\disable_realtime.ps1" -ForegroundColor Yellow
