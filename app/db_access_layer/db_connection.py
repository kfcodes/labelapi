import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv("env/pallet_label.env")

usr = os.getenv("USR")
pwd = os.getenv("PASSWORD")
hst = os.getenv("HOST")
prt = os.getenv("PORT")
data_base = os.getenv("DATABASE")

connection_string = f'mariadb+pymysql://{usr}:{pwd}@{hst}:{prt}/{data_base}'

def db():
    engine = create_engine(connection_string)
    return engine;
