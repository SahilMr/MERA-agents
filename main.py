from fastapi import FastAPI
from contextlib import asynccontextmanager
from rti_agentic_system.config.database import engine, Base
from rti_agentic_system.routers import rti_endpoints


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up resources if necessary

app = FastAPI(title="RTI Agentic System", lifespan=lifespan)

app.include_router(rti_endpoints.router, prefix="/api/rti", tags=["RTI"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the RTI Agentic System API"}
