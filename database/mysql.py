# -*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function

from collections import deque
import warnings
import logging

from tornado.ioloop import IOLoop
from tornado.gen import coroutine, Return
from tornado.concurrent import Future

from tornado_mysql import connect
from tornado_mysql.connections import Connection
from defines.config import *
from tornado_mysql import pools

log = logging.getLogger("tornado_mysql.pools")

class Mysql:
    def __init__(self):
        self._pool = pools.Pool(dict(host=DB_HOST, port=DB_PORT,
                                     user=DB_USER, passwd=DB_PASSWORD,
                                     db=DB_DATABASE),
                                max_idle_connections=1,
                                max_recycle_sec=3)

    @property
    def pool(self):
        return self._pool

    def __error_log(self, sqlstr, parm=None, error=None):
        logging.error('[sqlerror]sql is: {0}\nparms is:{1}\nerror is:{2}'.format(sqlstr, parm, error))

    def __format_sql(self, sql_str, parm=None):
        _parm = []
        if parm is not None:
            for p in parm:
                _parm.append("'%s'" % p)
            out_str = sql_str % tuple(_parm)
        else:
            out_str = sql_str
        return out_str

    def __print_sql(self, sql_str, parm=None):
        """打印完整的sql语句，方便调试"""

        out_str = self.__format_sql(sql_str, parm)
        logging.debug(sql_str)

    async def query(self, sql_str):
        result = []
        try:
            self.__print_sql(sql_str)
            cursor = await self.pool.execute(sql_str)
            _fetch = cursor.fetchall()
            if _fetch:
                result = _fetch
        except Exception as e:
            self.__error_log(sql_str, (), repr(e))

        return result

    async def exec_safe(self, sql_str: str, args) -> bool:
        result = True

        try:
            self.__print_sql(sql_str, args)
            cursor = await self.pool.execute(sql_str, args)
            return cursor.rowcount

        except Exception as e:
            self.__error_log(sql_str, args, repr(e))
            result = False

        finally:
            return result


class Transaction(object):
    """Represents transaction in pool"""
    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn

    def _ensure_conn(self):
        if self._conn is None:
            raise Exception("Transaction is closed already")

    def _close(self):
        self._pool._put_conn(self._conn)
        self._pool = self._conn = None

    @coroutine
    def execute(self, query, args=None):
        """
        :return: Future[Cursor]
        :rtype: Future
        """
        self._ensure_conn()
        cur = self._conn.cursor()
        yield cur.execute(query, args)
        raise Return(cur)

    @coroutine
    def commit(self):
        self._ensure_conn()
        yield self._conn.commit()
        self._close()

    @coroutine
    def rollback(self):
        self._ensure_conn()
        yield self._conn.rollback()
        self._close()

    def __del__(self):
        if self._pool is not None:
            warnings.warn("Transaction has not committed or rollbacked.")
            log.warn("Transaction has not committed or rollbacked.")
            self._pool._close_conn(self._conn)