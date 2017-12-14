# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import random
from openerp.tests import common


class TestAuthSignup(common.TransactionCase):

    def setUp(self):
        super(TestAuthSignup, self).setUp()

    def test_signup(self):
        chars = ('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                 '0123456789')
        token = ''.join(
            random.SystemRandom().choice(chars) for i in xrange(20))
        values = {
            'token': token,
            'login': 'test',
            'name': 'test_name',
            'password': 'pass'}
        db, login, password = self.env['res.users'].signup(values)
