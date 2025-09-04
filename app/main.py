from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import items, projects, estimations

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Estimation Backend", version="1.0.0")

# CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

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

@app.get("/health")
def health():
    return {"status": "ok"}
