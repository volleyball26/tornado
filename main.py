# -*- coding:utf-8 -*-
import gc
import time
import logging
import signal

from tornado.options import define, options, parse_command_line
from tornado.util import basestring_type
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
import tornado.httpclient
import tornado.log
from tornado.log import app_log

from router import HANDLERS
from defines import *

tornado.httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')

define("port", default=80, help="run on the given port", type=int)
define("debug", default=0, help="user pdb", type=int)


class WebApplication(tornado.web.Application):
    """
    Web应用类，定义应用
    """

    def __init__(self, ioloop=tornado.ioloop.IOLoop.instance(), dsn=None, debug=False):
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            login_url="/user/login",
            # cookie_secret=COOKIE_SECRET,
        )
        super(WebApplication, self).__init__(HANDLERS, **settings)

class LogFormatter(tornado.log.LogFormatter):
    """修改默认输出日志格式"""

    def __init__(self, debug=True):
        super(LogFormatter, self).__init__(
            fmt='%(color)s[%(asctime)s %(levelname)s %(filename)s.%(lineno)s]%(end_color)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.debug = debug

    def format(self, record):
        if self.debug:
            formatted = super(LogFormatter, self).format(record)
            return formatted
        try:
            message = record.getMessage()
            assert isinstance(message, basestring_type)  # guaranteed by logging
            record.message = tornado.log._safe_unicode(message)
        except Exception as e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)

        record.asctime = self.formatTime(record, self.datefmt)
        record.message = record.message.replace('\n', '   ')

        if record.levelno in self._colors:
            record.color = self._colors[record.levelno]
            record.end_color = self._normal
        else:
            record.color = record.end_color = ''

        formatted = self._fmt % record.__dict__
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            lines = [formatted.rstrip()]
            lines.extend(tornado.log._safe_unicode(ln) for ln in record.exc_text.split('\n'))
            formatted = ''.join(lines)
        return formatted

class App:
    def __init__(self):
        self.http_server = None
        self.main_app = None
        self.io_loop = tornado.ioloop.IOLoop.instance()
        self.deadline = None

    def __del__(self):
        pass

    def sig_handler(self, sig, frame):  # pylint:disable=W0613
        """
        捕捉停止信号
        :param sig:
        :return:
        """
        logging.info('Caught signal: %s', sig)
        tornado.ioloop.IOLoop.instance().add_callback(self.shutdown)

    def shutdown(self):
        """
        停止app
        :return:
        """
        logging.info('Stopping http server')
        if self.http_server is not None:
            self.http_server.stop()  # 不接收新的 HTTP 请求

        logging.info('Will shutdown in %s seconds ...', 1)

        self.deadline = time.time() + 1
        self.stop_loop()

    def stop_loop(self):
        """
        停止主循环
        :return:
        """
        now = time.time()
        if now < self.deadline:
            self.io_loop.add_timeout(now + 1, self.stop_loop)
        else:
            app_log.info('Server Shutdown!')
            self.io_loop.stop()  # 处理完现有的 callback 和 timeout 后，可以跳出 io_loop.start() 里的循环

    def init(self):
        """
        初始化app
        :return:
        """
        # importlib.reload(sys)
        # sys.setdefaultencoding('utf-8')

        # register signal.SIGTSTP's handler
        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGQUIT, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)
        signal.signal(signal.SIGTSTP, self.sig_handler)
        return True

    @staticmethod
    def init_log():
        debug_log = logging.getLogger('debug')
        if APP_ENV == 'master':
            debug_log.setLevel(logging.CRITICAL)
        else:
            debug_log.setLevel(logging.DEBUG)
        logging.info('init log done')

    def main_loop(self):
        """
        启动主循环
        :return:
        """
        parse_command_line()
        # 日志格式设置
        self.init_log()
        [i.setFormatter(LogFormatter()) for i in logging.getLogger().handlers]
        # [i.setFormatter(LogFormatter()) for i in logging.getLogger().handlers]
        # 设计调试日志的日志格式 # 暂时无法解决重复输入日志的问题
        # debug_fmt = tornado.log.LogFormatter(
        #     fmt='%(color)s[%(asctime)s %(funcName)s %(levelname)s]%(end_color)s %(message)s', datefmt='%H:%M:%S')
        if options.debug == 1:
            import pdb
            pdb.set_trace()  # 引入相关的pdb模块

        logging.info('Init Server...')
        self.main_app = WebApplication(debug=APP_ENV != 'master')
        self.http_server = tornado.httpserver.HTTPServer(self.main_app, xheaders=True)
        self.http_server.listen(options.port)

        # 清除垃圾
        tornado.ioloop.PeriodicCallback(gc_memory_check,60*60*1000).start()

        logging.info('Server Running in port %s...', options.port)
        self.io_loop.start()

def gc_memory_check():
    gc.collect()
    if len(gc.garbage) > 0:
        logging.warning("[gc stat]: {} objects in garbage".format(len(gc.garbage)))
    else:
        logging.info("[gc stat]: No memory leaks found!")


if __name__ == '__main__':
    APP = App()
    if APP.init():
        APP.main_loop()
