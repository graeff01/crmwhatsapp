import os
import platform
import subprocess
import time

print("🚀 Iniciando CRM WhatsApp Veloce...")

BASE_PATH = os.path.expanduser("~/Desktop/crm-whatsapp")
SYSTEM = platform.system().lower()

# ========= BACKEND =========
print("🔹 Iniciando Backend (Flask)...")
backend_path = os.path.join(BASE_PATH, "backend")
activate_cmd = ""

if "windows" in SYSTEM:
    activate_cmd = f"{backend_path}\\.venv\\Scripts\\activate && python app.py"
else:
    activate_cmd = f"cd {backend_path} && source venv/bin/activate && python3 app.py"

subprocess.Popen(activate_cmd, shell=True)
time.sleep(3)

# ========= WHATSAPP SERVICE =========
print("🔹 Iniciando WhatsApp Service (Node)...")
whatsapp_path = os.path.join(BASE_PATH, "whatsapp-service")
subprocess.Popen(f"cd {whatsapp_path} && npm start", shell=True)
time.sleep(3)

# ========= FRONTEND =========
print("🔹 Iniciando Frontend (React/Vite)...")
frontend_path = os.path.join(BASE_PATH, "frontend")
subprocess.Popen(f"cd {frontend_path} && npm run dev", shell=True)

print("\n✅ Todos os serviços foram iniciados com sucesso!")
print("🌐 Acesse: http://localhost:5173")
