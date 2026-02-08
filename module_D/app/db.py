from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


uri = "postgresql+asyncpg://arthur:146a@localhost:5432/track_analysis"
engine = create_async_engine(uri)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session