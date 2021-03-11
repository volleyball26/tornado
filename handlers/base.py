# -*- coding:utf-8 -*-
import json

from tornado.web import RequestHandler, Finish

from database.mysql import Mysql
from database.postgresql import PostgreSQL
from utils.utils import json_dumps
from defines.code_msg import SUCCESS_CODE, MISS_PARAMS_ERROR_CODE, PARAM_ERROR_CODE


class BaseHandler(RequestHandler, PostgreSQL):

    @property
    def log(self):
        return self.application.bussiness_log

    def response(self, code, msg=None, **kwargs):
        """
        响应请求并finish连接
        :param code:
        :param msg:
        :param kwargs:
        :return:
        """
        # 默认返回json的数据类型
        self.add_header('Content-Type', 'application/json')
        data = {"code": code}
        if msg is not None:
            data['msg'] = msg
            if code != SUCCESS_CODE:
                self.log.warning('WARNING: %s', msg)
        for k, v in kwargs.items():
            data[k] = v
        self.finish(json_dumps(data))

    def get_param(self, argument, argument_default=None):
        """获取参数健壮版"""
        param = self.get_argument(argument, argument_default)
        if not param:
            param = argument_default
        # param = utils.WordCheck.wash_sql_params(param)
        return param

    _ARG_DEFAULT = object()

    def get_page_limit_offset(self, page, limit):
        try:
            limit = limit
            offset = (page - 1) * limit
        except Exception as e:
            limit, offset = 0, 0

        return [page, limit, offset]

    def get_json_param(self, argument, argument_default=_ARG_DEFAULT, wash=False, enum_list=None):
        """
        获取application/json的参数
        1.0.1 增加了必传参数的校验
        :param argument: 参数名
        :param argument_default: 参数默认值，不传时默认是必填参数
        :return: string 获取的参数值
        """
        try:
            # replace_str = self.request.body.replace(r'\u0000', '')
            args = json.loads(self.request.body)
        except:
            args = {}
        if not isinstance(args, dict):
            raise Finish(json_dumps({'code': MISS_PARAMS_ERROR_CODE, 'msg': '参数格式错误'}))
        param = args.get(argument)
        if param is None:
            if argument_default is self._ARG_DEFAULT:
                raise Finish(json_dumps({'code': MISS_PARAMS_ERROR_CODE, 'msg': '参数错误：缺少参数{}'.format(argument)}))
                # self.response(400,'参数错误：缺少参数{}'.format(argument))
                # return
            param = argument_default
        elif enum_list is not None:
            if param not in enum_list:
                raise Finish(json_dumps({'code': PARAM_ERROR_CODE, 'msg': '参数错误：{}不在支持的枚举值中'.format(argument)}))
        return param