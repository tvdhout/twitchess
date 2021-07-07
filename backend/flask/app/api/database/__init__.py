import os
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from app.api.database.models import *

engine = create_engine(f"{os.getenv('RSC_DATABASE_URL')}")
Session = sessionmaker(bind=engine)  # Session factory

user_mapping = {
    user: RandomSubscriberChallenge.make_subscriber_table(user)
    for user in os.getenv('USERS').split(':')
}


# Create tables if not exists
Base.metadata.create_all(bind=engine)
