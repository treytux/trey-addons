# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp.tests import common
from openerp import fields
import logging
_log = logging.getLogger(__name__)


class TestPosCloseSession(common.TransactionCase):

    def setUp(self):
        super(TestPosCloseSession, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            # 'property_account_receivable': self.accounts_430.id,
            # 'property_account_payable': self.accounts_430.id,
            'zip': 88,
            'city': 'CITY',
            'fax': '+36999999',
            'street': 'Calle Real, 33',
            'country_id': self.res_country_state.id,
            'state_id': self.res_country_state.id,
            'phone': '666225522'})
        tax21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.env.user.company_id.id})
        self.product = self.env['product.product'].create({
            'name': 'Product 01',
            'type': 'consu',
            'list_price': 10,
            'default_code': '123456',
            'taxes_id': [(6, 0, [tax21.id])]})

    def test_close_session(self):
        config = self.self.env['pos.config'].create({
            'name': 'PointOfSale',
            'receipt_header': 'HEADER<br/>FOR RECEIPT',
            'receipt_footer': 'FOOTER<br/>FOR RECEIPT'})
        session = self.env['pos.session'].create({
            'user_id': self.env.user.id,
            'name': self.env.user.name,
            'config_id': config.id})
        session.open_cb()
        order = self.env['pos.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.env.user.company_id.id,
            'session_id': session.id,
            'statement_ids': [(6, 0, [self.statement.id])],
            'date_order': fields.Date.today()})
        self.env['pos.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'company_id': self.env.user.company_id.id,
            'price_unit': self.product.list_price,
            'qty': 3.0,
            'name': self.product.name})
        order.signal_workflow('paid')
        self.assertEqual(self.pos_session.state, 'opened')
