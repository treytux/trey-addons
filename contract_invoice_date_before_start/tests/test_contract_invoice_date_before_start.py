###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests import common


class TestContractInvoiceDateBeforeStart(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'company_id': self.env.user.company_id.id,
            'name': 'Test product 1',
            'standard_price': 10,
            'default_code': '01-PROD',
            'list_price': 100,
        })

    def test_contract_invoice_visibility(self):
        contract = self.env['contract.contract'].create({
            'name': 'CRTTEST',
            'partner_id': self.partner.id,
        })
        contract_line = self.env['contract.line'].create({
            'name': 'Contract line test',
            'product_id': self.product.id,
            'contract_id': contract.id,
            'quantity': 1,
            'price_unit': 50,
            'is_recurring_note': True,
            'recurring_next_date': fields.Date.today() + timedelta(days=1),
            'recurring_rule_type': 'monthly',
            'date_start': fields.Date.today() + timedelta(days=1),
            'date_end': fields.Date.today() + timedelta(days=366),
        })
        self.assertTrue(contract_line.date_start)
        self.assertTrue(contract_line.date_end)
        today = fields.Date.today()
        self.assertFalse(today >= contract_line.date_start)
        self.assertTrue(contract_line.create_invoice_visibility)
        self.assertTrue(contract.create_invoice_visibility)
