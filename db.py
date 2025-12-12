import psycopg2

DB_CONFIG = dict(
    dbname="memory_app",
    user="S_MnCu",
    password="",
    host="localhost",
    port=1145,
)

def get_conn():
    return psycopg2.connect(**DB_CONFIG)
