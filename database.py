from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


from config import *

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async_engine = create_async_engine(url=DATABASE_URL, echo=True, pool_size=5,
                             max_overflow=10) #pool_size  максимальное колличество подкючений
                                            # max_overflow еще дополнительные соединения


async_session = async_sessionmaker(async_engine)


class Base(DeclarativeBase):
    type_annotation_map = {

    }

    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        """Relationships не используются в repr(), т.к. могут вести к неожиданным подгрузкам"""
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"




# async def get_async_session():
#     async with async_session() as session:
#         yield session
