from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, SessionLocal
from .routers import items, projects, estimations
from .seed import seed_data
from .models import Item, Division

# Create tables
Base.metadata.create_all(bind=engine)

# Seed data if tables are empty
db = SessionLocal()
if not db.query(Item).count() and not db.query(Division).count():
    seed_data()
db.close()

app = FastAPI(title="Estimation Backend", version="1.0.0")

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

@app.get("/health")
def health():
    return {"status": "ok"}
