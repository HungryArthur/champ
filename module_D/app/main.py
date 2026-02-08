from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db, engine
from models import Track_analysis
from typing import List
from sqlalchemy import select

app = FastAPI()

@app.get("/")
async def root():
    return {"answer": "Hello World"}

@app.get("/data/{lat}&{lon}", response_model=List[dict])
async def read_items(lat: float, lon: float, db: AsyncSession = Depends(get_db)):
    stmt = select(Track_analysis).where(
        (Track_analysis.latitude == lat) & 
        (Track_analysis.longitude == lon)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return [{"track_id": item.track_id, "latitude": item.latitude, "longitude": item.longitude, "danger": item.danger, "difficult": item.difficult_level} for item in items]