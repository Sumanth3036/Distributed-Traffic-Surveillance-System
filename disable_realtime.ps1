# PowerShell script to disable real-time mode and revert to standard mode

Write-Host "🔄 Reverting to Standard Mode..." -ForegroundColor Cyan
Write-Host ""

# Check if backups exist
if (-not (Test-Path "frontend\app_backup.py")) {
    Write-Host "❌ No backup found! Cannot revert." -ForegroundColor Red
    Write-Host "   The system is already in standard mode or backups were deleted." -ForegroundColor Yellow
    exit 1
}

# Restore from backups
Write-Host "📦 Restoring from backups..." -ForegroundColor Yellow
Copy-Item "frontend\app_backup.py" "frontend\app.py" -Force
Copy-Item "master_worker\master_worker_backup.py" "master_worker\master_worker.py" -Force
Write-Host "✅ Files restored" -ForegroundColor Green
Write-Host ""

# Restart services
Write-Host "🔄 Restarting services..." -ForegroundColor Yellow
docker-compose restart streamlit_ui api_server master_worker

Write-Host ""
Write-Host "✅ Standard Mode Restored!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access the standard UI at: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 To enable real-time mode again, run: .\enable_realtime.ps1" -ForegroundColor Yellow
