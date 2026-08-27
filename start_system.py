"""
Sonaris AI — Master Application Launcher
Starts both the FastAPI backend and Vite frontend concurrently.
"""
import subprocess
import sys
import time
import os
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main():
    print("=" * 65)
    print("      SONARIS AI — UNDERWATER INTELLIGENCE PLATFORM")
    print(" AI-Powered Side-Scan Sonar Marine Debris & Risk Prioritization")
    print("=" * 65)
    print("\n[1/3] Initializing environment and verifying database...")

    python_exe = sys.executable

    # Pre-seed DB check
    try:
        from backend.app.models.database import init_db, SessionLocal, Survey
        from backend.app.api.routes import api_generate_demo_surveys
        init_db()
        db = SessionLocal()
        if db.query(Survey).count() == 0:
            print("      Synthesizing initial realistic sonar survey datasets...")
            api_generate_demo_surveys()
            print("      Seeding complete.")
        db.close()
    except Exception as e:
        print(f"      Startup check notice: {e}")

    print("\n[2/3] Starting FastAPI Backend on http://localhost:8000 ...")
    backend_proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(BASE_DIR),
    )

    time.sleep(2)

    print("\n[3/3] Starting React/Vite Frontend on http://localhost:5173 ...")
    frontend_dir = BASE_DIR / "frontend"
    frontend_cmd = "npm run dev"
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(frontend_dir),
        shell=True
    )

    print("\n" + "=" * 65)
    print(" SONARIS AI IS NOW RUNNING!")
    print(" -> Frontend GIS Dashboard: http://localhost:5173")
    print(" -> Backend API Swagger UI: http://localhost:8000/docs")
    print("=" * 65)
    print(" Press Ctrl+C to terminate all services.\n")

    try:
        time.sleep(3)
        webbrowser.open("http://localhost:5173")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Sonaris AI services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
