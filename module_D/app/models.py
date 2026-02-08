from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from db import engine

class Base(DeclarativeBase):
    pass

class Track_analysis(Base):
    __tablename__ = "track_analysis"
    track_id = Column(Integer, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    danger = Column(Integer)
    difficult_level = Column(Integer)