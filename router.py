# -*- coding:utf-8 -*-
from tornado.web import RequestHandler


class TEST(RequestHandler):
    async def get(self):
        self.finish("hellworld")
        return
    
HANDLERS = [
    (r"/logo", TEST),
]