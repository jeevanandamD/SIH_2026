from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .models.database import init_db, SessionLocal, Survey
from .api.routes import router, api_generate_demo_surveys
from .config import DATA_DIR

app = FastAPI(
    title="Sonaris AI",
    description="AI-Powered Side-Scan Sonar Marine Debris & Underwater Anomaly Detection System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")
app.include_router(router, prefix="/api")


@app.on_event("startup")
def startup():
    init_db()
    db = SessionLocal()
    try:
        count = db.query(Survey).count()
        if count == 0:
            print("Seeding initial realistic Sonaris AI surveys...")
            api_generate_demo_surveys()
            print("Successfully initialized Sonaris AI database with demo surveys.")
    except Exception as e:
        print(f"Startup check notice: {e}")
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "system": "Sonaris AI",
        "tagline": "AI-Powered Side-Scan Sonar Marine Debris & Underwater Anomaly Detection System",
        "status": "online",
        "version": "1.0.0"
    }
