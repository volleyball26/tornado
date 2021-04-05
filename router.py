# -*- coding:utf-8 -*-
from tornado.web import RequestHandler
from handlers.base import BaseHandler


class TEST(BaseHandler):
    async def get(self):
        page = self.get_param("page", 1)
        limit = self.get_param("limit", 10)
        sql = """ select * from users """
        # result = await self.query(sql)
        result = {"name": "jack", "sex": "女"}
        page, limit, offset = self.get_page_limit_offset(page, limit)
        self.response(200, {"page":page, "limit":limit, "offset": offset, "result":result})
        return
    
HANDLERS = [
    (r"/logo", TEST),
]