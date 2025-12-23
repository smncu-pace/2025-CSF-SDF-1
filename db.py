<<<<<<< HEAD
# -*- coding: utf-8 -*-
import psycopg2
=======

>>>>>>> bdcb56f427e2b4c737874f0a525c1ed4efea7fa9
from psycopg2.extras import RealDictCursor
from config import Config

def get_db_connection():
    conn = psycopg2.connect(
        Config.DATABASE_URL,
        cursor_factory=RealDictCursor
    )
    return conn
<<<<<<< HEAD
=======

>>>>>>> bdcb56f427e2b4c737874f0a525c1ed4efea7fa9
