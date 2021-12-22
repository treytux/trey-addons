###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests.common import TransactionCase


class TestContractLineMarkers(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.contract = self.env['contract.contract'].create({
            'name': 'Test contract',
            'partner_id': self.partner.id,
            'code': 'test code'
        })
        self.line_obj = self.env['contract.line']
        self.line = self.line_obj.new({
            'name': 'Test contract',
            'contract_id': self.contract.id,
            'product_id': self.product.id,
            'recurring_next_date': fields.Date.today(),
            'quantity': 1,
            'date_end': datetime.today().date() + relativedelta(months=5),
        })
        self.line._onchange_product_id()
        self.line = self.line_obj.create(
            self.line_obj._convert_to_write(self.line._cache))

    def test_contract_marks(self):
        self.contract.write({
            'code': '#MONTH_STR#-#MONTH_INT#-#YEAR#'
        })
        first_date_invoice = self.contract.recurring_next_date
        invoice = self.contract.recurring_create_invoice()
        self.assertEquals(
            first_date_invoice.strftime('%B-%m-%Y').capitalize(),
            invoice.name)

    def test_line_contract_marks_start_dates(self):
        self.line.write({
            'name': '#START_MONTH_STR#-#START_MONTH_INT#-#START_YEAR#',
        })
        invoice = self.contract.recurring_create_invoice()
        self.assertEquals(
            self.line.date_start.strftime('%B-%m-%Y').capitalize(),
            invoice.invoice_line_ids[0].name)

    def test_line_contract_marks_end_dates(self):
        self.line.write({
            'name': '#END_MONTH_STR#-#END_MONTH_INT#-#END_YEAR#',
        })
        invoice = self.contract.recurring_create_invoice()
        self.assertEquals(
            self.line.recurring_next_date.strftime('%B-%m-%Y').capitalize(),
            invoice.invoice_line_ids[0].name)
