###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import common


class TestContractLineLot(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'default_code': '01-PROD',
            'list_price': 100,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 2',
            'standard_price': 10,
            'default_code': '02-PROD',
            'list_price': 50,
        })
        self.company = self.env.company
        self.lot_01 = self.env['stock.lot'].create({
            'name': '123456789',
            'product_id': self.product_01.id,
            'company_id': self.company.id,
        })
        self.lot_02 = self.env['stock.lot'].create({
            'name': '987654321',
            'product_id': self.product_02.id,
            'company_id': self.company.id,
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')

    def set_quantity_in_location(self, product, location, qty, lot=None):
        self.env['stock.quant']._update_available_quantity(
            product, location, qty, lot_id=lot
        )

    def test_contract_line_without_date_end(self):
        self.set_quantity_in_location(
            self.product_01, self.stock_location, 10, lot=self.lot_01)
        contract = self.env['contract.contract'].create({
            'name': 'Test contract',
            'partner_id': self.partner.id,
        })
        self.assertEqual(len(contract.contract_line_ids), 0)
        contract_line = self.env['contract.line'].create({
            'name': 'Contract line test',
            'product_id': self.product_01.id,
            'contract_id': contract.id,
            'quantity': 1,
            'price_unit': 50,
            'recurring_rule_type': 'quarterly',
            'date_start': fields.Date.today(),
        })
        self.assertTrue(contract_line.date_start)
        self.assertFalse(contract_line.date_end)
        self.assertEqual(len(contract.contract_line_ids), 1)
        self.assertEqual(
            len(contract.contract_line_ids.mapped('lot_ids')), 0)
        self.assertEqual(len(self.lot_01.contract_line_ids), 0)
        contract_line.write({
            'lot_ids': [(4, self.lot_01.id)],
        })
        self.assertEqual(
            len(contract.contract_line_ids.mapped('lot_ids')), 1)
        self.lot_01._compute_contract_line_ids()
        self.lot_01._compute_last_location_id()
        self.assertEqual(len(self.lot_01.contract_line_ids), 1)
        self.assertEqual(self.lot_01.last_contract_id, contract)
        self.assertEqual(self.lot_01.last_contract_line_id, contract_line)
        self.assertEqual(
            self.lot_01.last_contract_product_id, contract_line.product_id)
        self.assertEqual(
            self.lot_01.last_contract_date_start, contract_line.date_start)
        self.assertEqual(
            self.lot_01.last_contract_date_end, contract_line.date_end)
        self.assertFalse(
            self.lot_01.last_contract_date_end)
        self.assertEqual(self.lot_01.last_location_id, self.stock_location)

    def test_contract_multiple_lines_with_lot(self):
        self.set_quantity_in_location(
            self.product_01, self.stock_location, 1, lot=self.lot_01)
        self.set_quantity_in_location(
            self.product_02, self.stock_location, 1, lot=self.lot_02)
        contract = self.env['contract.contract'].create({
            'name': 'Test contract',
            'partner_id': self.partner.id,
        })
        self.assertEqual(len(contract.contract_line_ids), 0)
        contract_line_01 = self.env['contract.line'].create({
            'name': 'Contract line test',
            'product_id': self.product_01.id,
            'contract_id': contract.id,
            'quantity': 1,
            'price_unit': 50,
            'recurring_rule_type': 'quarterly',
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(months=12),
        })
        contract_line_02 = self.env['contract.line'].create({
            'name': 'Contract line test 2',
            'product_id': self.product_02.id,
            'contract_id': contract.id,
            'quantity': 1,
            'price_unit': 80,
            'recurring_rule_type': 'quarterly',
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(months=12),
        })
        self.assertEqual(len(contract.contract_line_ids), 2)
        self.assertEqual(
            len(contract.contract_line_ids.mapped('lot_ids')), 0)
        self.assertEqual(len(self.lot_01.contract_line_ids), 0)
        self.assertEqual(len(self.lot_02.contract_line_ids), 0)
        contract_line_01.write({
            'lot_ids': [(6, 0, [self.lot_01.id])],
        })
        contract_line_02.write({
            'lot_ids': [(6, 0, [self.lot_02.id])],
        })
        self.assertEqual(
            len(contract.contract_line_ids.mapped('lot_ids')), 2)
        self.lot_01._compute_contract_line_ids()
        self.lot_01._compute_last_location_id()
        self.assertEqual(len(self.lot_01.contract_line_ids), 1)
        self.assertEqual(self.lot_01.last_contract_id, contract)
        self.assertEqual(self.lot_01.last_contract_line_id, contract_line_01)
        self.assertEqual(
            self.lot_01.last_contract_product_id, contract_line_01.product_id)
        self.assertEqual(
            self.lot_01.last_contract_date_start, contract_line_01.date_start)
        self.assertEqual(
            self.lot_01.last_contract_date_end, contract_line_01.date_end)
        self.assertEqual(self.lot_01.last_location_id, self.stock_location)
        self.lot_02._compute_contract_line_ids()
        self.lot_02._compute_last_location_id()
        self.assertEqual(len(self.lot_02.contract_line_ids), 1)
        self.assertEqual(self.lot_02.last_contract_id, contract)
        self.assertEqual(self.lot_02.last_contract_line_id, contract_line_02)
        self.assertEqual(
            self.lot_02.last_contract_product_id, contract_line_02.product_id)
        self.assertEqual(
            self.lot_02.last_contract_date_start, contract_line_02.date_start)
        self.assertEqual(
            self.lot_02.last_contract_date_end, contract_line_02.date_end)
        self.assertEqual(self.lot_02.last_location_id, self.stock_location)

    def test_contract_line_multiple_lot(self):
        self.set_quantity_in_location(
            self.product_01, self.stock_location, 1, lot=self.lot_01)
        self.set_quantity_in_location(
            self.product_02, self.stock_location, 1, lot=self.lot_02)
        contract = self.env['contract.contract'].create({
            'name': 'Test contract',
            'partner_id': self.partner.id,
        })
        self.assertEqual(len(contract.contract_line_ids), 0)
        contract_line = self.env['contract.line'].create({
            'name': 'Contract line test',
            'product_id': self.product_01.id,
            'contract_id': contract.id,
            'quantity': 1,
            'price_unit': 50,
            'recurring_rule_type': 'quarterly',
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(months=12),
        })
        self.assertEqual(len(contract.contract_line_ids), 1)
        self.assertEqual(
            len(contract.contract_line_ids.mapped('lot_ids')), 0)
        self.assertEqual(len(self.lot_01.contract_line_ids), 0)
        self.assertEqual(len(self.lot_02.contract_line_ids), 0)
        contract_line.write({
            'lot_ids': [(6, 0, [self.lot_01.id, self.lot_02.id])],
        })
        self.assertEqual(
            len(contract.contract_line_ids.mapped('lot_ids')), 2)
        self.lot_01._compute_contract_line_ids()
        self.lot_01._compute_last_location_id()
        self.assertEqual(len(self.lot_01.contract_line_ids), 1)
        self.assertEqual(self.lot_01.last_contract_id, contract)
        self.assertEqual(self.lot_01.last_contract_line_id, contract_line)
        self.assertEqual(
            self.lot_01.last_contract_product_id, contract_line.product_id)
        self.assertEqual(
            self.lot_01.last_contract_date_start, contract_line.date_start)
        self.assertEqual(
            self.lot_01.last_contract_date_end, contract_line.date_end)
        self.assertEqual(self.lot_01.last_location_id, self.stock_location)
        self.lot_02._compute_contract_line_ids()
        self.lot_02._compute_last_location_id()
        self.assertEqual(len(self.lot_02.contract_line_ids), 1)
        self.assertEqual(self.lot_02.last_contract_id, contract)
        self.assertEqual(self.lot_02.last_contract_line_id, contract_line)
        self.assertEqual(
            self.lot_02.last_contract_product_id, contract_line.product_id)
        self.assertEqual(
            self.lot_02.last_contract_date_start, contract_line.date_start)
        self.assertEqual(
            self.lot_02.last_contract_date_end, contract_line.date_end)
        self.assertEqual(self.lot_02.last_location_id, self.stock_location)

    def test_contract_line_one_lot(self):
        self.set_quantity_in_location(
            self.product_01, self.stock_location, 10, lot=self.lot_01)
        contract = self.env['contract.contract'].create({
            'name': 'Test contract',
            'partner_id': self.partner.id,
        })
        self.assertEqual(len(contract.contract_line_ids), 0)
        contract_line = self.env['contract.line'].create({
            'name': 'Contract line test',
            'product_id': self.product_01.id,
            'contract_id': contract.id,
            'quantity': 1,
            'price_unit': 50,
            'recurring_rule_type': 'quarterly',
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(months=12),
        })
        self.assertEqual(len(contract.contract_line_ids), 1)
        self.assertEqual(
            len(contract.contract_line_ids.mapped('lot_ids')), 0)
        self.assertEqual(len(self.lot_01.contract_line_ids), 0)
        contract_line.write({
            'lot_ids': [(4, self.lot_01.id)],
        })
        self.assertEqual(
            len(contract.contract_line_ids.mapped('lot_ids')), 1)
        self.lot_01._compute_contract_line_ids()
        self.lot_01._compute_last_location_id()
        self.assertEqual(len(self.lot_01.contract_line_ids), 1)
        self.assertEqual(self.lot_01.last_contract_id, contract)
        self.assertEqual(self.lot_01.last_contract_line_id, contract_line)
        self.assertEqual(
            self.lot_01.last_contract_product_id, contract_line.product_id)
        self.assertEqual(
            self.lot_01.last_contract_date_start, contract_line.date_start)
        self.assertEqual(
            self.lot_01.last_contract_date_end, contract_line.date_end)
        self.assertEqual(self.lot_01.last_location_id, self.stock_location)
