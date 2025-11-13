# start.ps1
Write-Host "🚀 Iniciando CRM WhatsApp..." -ForegroundColor Green

# Terminal 1 - Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python app.py"

# Terminal 2 - WhatsApp Service
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd whatsapp-service; npm start"

# Terminal 3 - Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "✅ Todos os serviços iniciados!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan