from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import ARRAY

from app.api.database.models import Base

__all__ = ['Authentication', 'User', 'StateToken']


class Authentication(Base):
    __tablename__ = 'authentication'

    user = Column(String(30), primary_key=True)
    userid = Column(Integer, nullable=False)
    accesstoken = Column(String(30), nullable=False)
    refreshtoken = Column(String(50))
    scope = Column(ARRAY(String))
    tokentype = Column(String)

    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f'Authentication(user={self.user}, scope={str(self.scope)})'


class User(Base):
    __tablename__ = 'users'

    username = Column(String(30), primary_key=True)
    token = Column(String(40))
    last_purged = Column(DateTime, default=datetime.now())


class StateToken(Base):
    __tablename__ = 'states'

    datetime = Column(DateTime, default=datetime.now())
    state = Column(String(64), primary_key=True)

    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
