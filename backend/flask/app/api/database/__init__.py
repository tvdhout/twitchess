import os
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from app.api.database.models import *

engine = create_engine(f"{os.getenv('DATABASE_URL')}")
Session = sessionmaker(bind=engine)  # Session factory

# Create tables if not exists
Base.metadata.create_all(bind=engine)
