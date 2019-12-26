# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import requests


class Methabook(object):
    name = 'methabook'

    def __init__(self, url, key):
        self.url = url
        self.key = key

    def open_url(self, url, data=None):
        if data is None:
            data = {}
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Api-Key': self.key}
        res = requests.get(url, headers=headers)
        return res
