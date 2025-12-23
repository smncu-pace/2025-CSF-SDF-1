# -*- coding: utf-8 -*-
import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config

def get_db_connection():
    conn = psycopg2.connect(
        Config.DATABASE_URL,
        cursor_factory=RealDictCursor
    )
    return conn
