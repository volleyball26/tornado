# -*- coding:utf-8 -*-
from tornado.web import RequestHandler
from handlers.base import BaseHandler


class TEST(BaseHandler):
    async def get(self):
        page = self.get_param("page", 1)
        limit = self.get_param("limit", 10)
        page, limit, offset = self.get_page_limit_offset(page, limit)
        self.response(100, {"page":page, "limit":limit, "offset": offset})
        return
    
HANDLERS = [
    (r"/logo", TEST),
]