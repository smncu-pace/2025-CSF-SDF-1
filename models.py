# -*- coding: utf-8 -*-
from flask import current_app
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    """
    获取一个新的数据库连接。
    返回 psycopg2 connection，对应 cursor 是 RealDickCursor，
    即查询结果是 dict 格式。
    """
    db_url = current_app.config["DATABASE_URL"]
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
