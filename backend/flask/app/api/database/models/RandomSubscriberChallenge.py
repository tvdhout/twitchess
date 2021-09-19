from sqlalchemy import Column, String
from app.api.database.models import Base


def make_subscriber_table(name: str) -> type:
    """
    Return a new SQLAlchemy Table object representing the lichess - twitch pairs for a certain user.
    """
    class Pair(Base):
        __tablename__ = name
        __table_args__ = {'extend_existing': True}

        twitch = Column(String(25), primary_key=True)
        lichess = Column(String(20), nullable=False)

        def dict(self):
            return {c.name: getattr(self, c.name) for c in self.__table__.columns}

        def __repr__(self):
            return f'{self.__tablename__.capitalize()} subscriber(twitch={self.twitch}, lichess={self.lichess})'
    return Pair
