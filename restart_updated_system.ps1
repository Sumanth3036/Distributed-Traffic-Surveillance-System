# PowerShell script to restart the updated Traffic Surveillance System

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Traffic Surveillance System Restart  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Step 1: Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "🔨 Step 2: Rebuilding containers with updated code..." -ForegroundColor Yellow
docker-compose build --no-cache streamlit_ui api_server master_worker

Write-Host ""
Write-Host "🚀 Step 3: Starting all services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "⏳ Step 4: Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "✅ System Status:" -ForegroundColor Green
docker-compose ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ System Ready!                      " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Access the system at:" -ForegroundColor Yellow
Write-Host "   http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "📖 Documentation:" -ForegroundColor Yellow
Write-Host "   - UPDATED_USER_GUIDE.md - Complete user guide" -ForegroundColor White
Write-Host "   - CHANGES_SUMMARY.md - What's changed" -ForegroundColor White
Write-Host ""
Write-Host "🎯 New Features:" -ForegroundColor Yellow
Write-Host "   ✅ Upload video/image" -ForegroundColor White
Write-Host "   ✅ Download processed output with detection blocks" -ForegroundColor White
Write-Host "   ✅ Color-coded bounding boxes (Green/Yellow/Red)" -ForegroundColor White
Write-Host "   ✅ Comprehensive detection statistics" -ForegroundColor White
Write-Host ""
Write-Host "📊 To view logs:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "🛑 To stop the system:" -ForegroundColor Yellow
Write-Host "   docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "Happy traffic monitoring! 🚦🚗" -ForegroundColor Green
