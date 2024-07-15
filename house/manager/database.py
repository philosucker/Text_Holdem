from sqlalchemy import create_engine, MetaData
from databases import Database

DATABASE_URL = "mysql+aiomysql://username:password@localhost/dbname"

database = Database(DATABASE_URL)
metadata = MetaData()

def get_engine():
    return create_engine(DATABASE_URL)
