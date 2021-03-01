# -*- coding:utf-8 -*-
import os
import string
import time
import random
from base64 import b64encode
import json
import datetime
import logging

LOG = logging.getLogger('debug')


class CJsonEncoder(json.JSONEncoder):
    """
    json encoder
    """

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


def generate_random_string(length, with_punctuation=True, with_digit=True):

    punctuation = '!$%^&*'
    random.seed(str(time.time()) + b64encode(os.urandom(32)).decode('utf-8'))

    rdw_seed = string.ascii_letters

    if with_digit:
        rdw_seed += string.digits

    if with_punctuation:
        rdw_seed += punctuation

    rdw = []
    while len(rdw) < length:
        rdw.append(random.choice(rdw_seed))
    return ''.join(rdw)


def create_uuid(prefix=None, uuid_len=12, with_punctuation=False, islower=True):
    """

    :param prefix:
    :param uuid_len:
    :param with_punctuation:
    :param islower:
    :return:
    """
    _str = generate_random_string(uuid_len, with_punctuation)
    if prefix is None:
        out_str = _str
    else:
        out_str = f'{prefix}_{_str}'
    if islower:
        out_str = out_str.lower()
    else:
        out_str = out_str.upper()
    return out_str


def json_dumps(data_dict):
    """

    :param data_dict:
    :return:
    """
    try:
        json_str = json.dumps(data_dict, cls=CJsonEncoder)
    except Exception as e:
        LOG.error(e)
        json_str = '{}'
    return json_str