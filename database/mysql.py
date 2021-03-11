# -*- coding:utf-8 -*-
from __future__ import print_function
import logging

from defines.config import *
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado_mysql import pools


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

    # @coroutine
    # def check_connect(self):
    #     return self.pool.

    def __error_log(self, sqlstr, parm=None, error=None):
        logging.error('[sqlerror]sql is: {0}\nparms is:{1}\nerror is:{2}'.format(sqlstr, parm, error))

    def __format_sql(self, sqlstr, parm=None):
        _parm = []
        if parm is not None:
            for p in parm:
                _parm.append("'%s'" % p)
            outstr = sqlstr % tuple(_parm)
        else:
            outstr = sqlstr
        return outstr

    def __print_sql(self, sqlstr, parm=None):
        """打印完整的sql语句，方便调试"""

        outstr = self.__format_sql(sqlstr, parm)
        logging.debug(outstr)
        # print('{}'.format(outstr))

    async def query(self, sqlstr):
        result = []
        try:
            self.__print_sql(sqlstr)
            cursor = await self.pool.execute(sqlstr)
            _fetch = cursor.fetchall()
            if _fetch:
                result = _fetch
        except Exception as e:
            self.__error_log(sqlstr, (), repr(e))

        return result