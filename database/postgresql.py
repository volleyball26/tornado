# coding:utf-8
"""
数据库基础模块
"""
import datetime

from psycopg2.extras import RealDictCursor
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.log import app_log
import momoko
import logging

from defines.config import DSN
logger = logging.getLogger('sql')


class PostGreSQLMiXin(object):
    """
    数据库基本操作类
    """

    def __init__(self, ioloop=None, max_size=2):

        if ioloop is None:
            ioloop = IOLoop.current()
        self._pool = momoko.Pool(
            dsn=DSN,
            cursor_factory=RealDictCursor,
            size=1,
            max_size=max_size,
            ioloop=ioloop,
            setsession=("SET TIME ZONE PRC",),
            raise_connect_errors=True,
            auto_shrink=True,
            shrink_delay=datetime.timedelta(seconds=10),
            shrink_period=datetime.timedelta(seconds=10)
        )

        if not ioloop.asyncio_loop.is_running():
            ioloop.run_sync(self._pool.connect)
            app_log.info('Connect Postgresql:{}'.format(self._pool.server_version))
        else:
            def check_result(future):
                conn = future.result()
                app_log.info('Connect Postgresql:{}'.format(conn.server_version))
            ioloop.add_future(self._pool.connect(), check_result)



    @property
    def pool(self):
        return self._pool

    @coroutine
    def check_connect(self):
        return self.pool.ping()

    def __error_log(self, sqlstr, parm=None, error=None):
        app_log.error('[sqlerror]sql is: {0}\nparms is:{1}\nerror is:{2}'.format(sqlstr, parm, error))

    def __format_sql(self,sqlstr, parm=None):
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
        logger.debug(outstr)
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
            # errormsg = '[sql_error]' + repr(e)
            # app_log.error(errormsg)

        return result

    async def query_safe(self, sqlstr, args):
        result = []
        try:
            self.__print_sql(sqlstr, args)
            cursor = await self.pool.execute(sqlstr, args)
            print(cursor)
            _fetch = cursor.fetchall()
            if _fetch:
                result = _fetch
        except Exception as e:
            # errormsg = '[sql_error]' + repr(e)
            # app_log.error(errormsg)
            self.__error_log(sqlstr, args, repr(e))

        return result

    async def find_safe(self, sqlstr, args):
        result = {}
        try:
            self.__print_sql(sqlstr, args)
            cursor = await self.pool.execute(sqlstr, args)
            _fetch = cursor.fetchone()
            if _fetch:
                result = _fetch
        except Exception as e:
            self.__error_log(sqlstr, args, repr(e))
            # errormsg = '[sql_error]' + repr(e)
            # app_log.error(errormsg)

        return result

    async def exec_safe(self, sqlstr: str, args) -> bool:
        result = True

        try:
            self.__print_sql(sqlstr, args)
            cursor = await self.pool.execute(sqlstr, args)
            return cursor.rowcount

        except Exception as e:
            self.__error_log(sqlstr, args, repr(e))
            # errormsg = '[sql_error]' + repr(e)
            # app_log.error(errormsg)
            result = False

        finally:
            return result

    def trans_begin(self):
        trans_obj = Transaction(self)
        return trans_obj

    async def trans_exec_many(self, trans_list):
        rv = True
        try:
            for sqlstr, params in trans_list:
                self.__print_sql(sqlstr, params)
            cursors = await self.pool.transaction(trans_list)
            if not cursors:
                rv = False

        except Exception as e:
            error_msg = ''
            for sqlstr, param in trans_list:
                error_msg += f'sql: {sqlstr}\n param: {param}\n'
            error_msg += '[errror]' + repr(e)
            app_log.error(error_msg)
            rv = False
        return rv


class Transaction(object):

    def __init__(self, db):
        self.db = db
        self.trans_list = []

    def trans_exec_safe(self, sqlstr, *params):
        sqltask = [sqlstr, params]
        self.trans_list.append(sqltask)

    async def trans_commit_safe(self):
        res = await self.db.trans_exec_many(self.trans_list)
        if res:
            # 成功后清空
            self.trans_list = []
        return res


