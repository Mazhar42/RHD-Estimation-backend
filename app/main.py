from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, SessionLocal
from .routers import items, projects, estimations, divisions
from .seed import seed_data
from .models import Item, Division



app = FastAPI(title="Estimation Backend", version="1.0.0")

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    # Check if divisions table is empty
    if db.query(Division).count() == 0:
        seed_data()
    db.close()

# CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(items.router)
app.include_router(projects.router)
app.include_router(estimations.router)
app.include_router(divisions.router)

@app.get("/health")
def health():
    return {"status": "ok"}
