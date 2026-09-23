###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import common


class TestContractLineEasyUnlink(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        product_template = self.env['product.template'].create({
            'name': 'Test Product',
            'type': 'service',
            'default_code': 'PROD_TEST',
            'list_price': 100.0,
            'standard_price': 50.0,
        })
        self.product = product_template.product_variant_ids[0]
        self.line_test_end = fields.Date.today() + relativedelta(months=6)
        self.contract_test = self.env['contract.contract'].create({
            'name': 'Test Contract 1',
            'partner_id': self.partner.id,
            'recurring_rule_type': 'monthly',
            'recurring_interval': 1,
            'date_start': fields.Date.today(),
            'date_end': self.line_test_end,
            'contract_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'price_unit': 100.0,
                    'name': 'Line A',
                    'date_start': fields.Date.today(),
                    'date_end': self.line_test_end,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 2,
                    'price_unit': 50.0,
                    'name': 'Line B',
                    'date_start': fields.Date.today(),
                    'date_end': self.line_test_end,
                }),
            ],
        })
        self.line_test = self.contract_test.contract_line_ids[0]
        self.line_test_2 = self.contract_test.contract_line_ids[1]
        self.contract_test_2 = self.env['contract.contract'].create({
            'name': 'Test Contract 2',
            'partner_id': self.partner.id,
            'recurring_rule_type': 'monthly',
            'recurring_interval': 1,
            'date_start': fields.Date.today(),
            'contract_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'price_unit': 200.0,
                    'name': 'Line C',
                    'date_start': fields.Date.today(),
                    'date_end': self.line_test_end,
                }),
            ],
        })
        self.line_test_3 = self.contract_test_2.contract_line_ids

    def test_cancel_single_line(self):
        self.line_test.cancel()
        self.assertTrue(self.line_test.is_canceled)
        self.assertFalse(self.line_test.is_auto_renew)
        self.assertTrue(self.contract_test.message_ids)
        self.assertIn(
            'Contract line canceled: <strong>Line A</strong>',
            self.contract_test.message_ids[0].body,)
        self.assertFalse(self.line_test.successor_contract_line_id)

    def test_cancel_multiple_lines_same_contract(self):
        lines = self.line_test + self.line_test_2
        lines.cancel()
        for line in lines:
            self.assertTrue(line.is_canceled)
            self.assertFalse(line.is_auto_renew)
        self.assertTrue(self.contract_test.message_ids)
        self.assertIn(
            'Contract line canceled: <strong>Line A</strong><br>- '
            '<strong>Line B</strong>',
            str(self.contract_test.message_ids[0].body))

    def test_cancel_multiple_lines_different_contracts(self):
        (self.line_test + self.line_test_3).cancel()
        messages_contract_test = self.contract_test.message_ids
        self.assertTrue(messages_contract_test)
        self.assertIn(
            'Contract line canceled: <strong>Line A</strong>',
            messages_contract_test[0].body)
        self.assertNotIn('Line C', messages_contract_test[0].body)
        messages_contract_test_2 = self.contract_test_2.message_ids
        self.assertTrue(messages_contract_test_2)
        self.assertIn(
            'Contract line canceled: <strong>Line C</strong>',
            messages_contract_test_2[0].body)

    def test_cancel_with_predecessor(self):
        line_successor = self.env['contract.line'].create({
            'contract_id': self.contract_test.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 150.0,
            'name': 'Successor Line',
        })
        successor_start = self.line_test_end + relativedelta(months=1)
        line_successor.write({
            'date_start': successor_start,
            'date_end': successor_start + relativedelta(months=1),
            'recurring_next_date': successor_start,
        })
        line_successor.write({
            'predecessor_contract_line_id': self.line_test.id,
        })
        self.line_test.write({
            'date_end': successor_start - relativedelta(months=1),
            'successor_contract_line_id': line_successor.id,
        })
        line_successor.cancel()
        self.assertFalse(self.line_test.successor_contract_line_id)
        self.assertTrue(line_successor.is_canceled)

    def test_stop_calls_cancel(self):
        result = self.line_test.stop(fields.Date.today())
        self.assertTrue(result)
        self.assertTrue(self.line_test.is_canceled)
        self.assertFalse(self.line_test.is_auto_renew)
        messages = self.contract_test.message_ids
        self.assertEqual(len(messages), 2)
        self.assertIn(
            'Contract line canceled: <strong>Line A</strong>',
            messages[0].body)
        result = self.line_test_2.stop(
            fields.Date.today(), manual_renew_needed=True, post_message=False)
        self.assertTrue(result)
        self.assertTrue(self.line_test_2.is_canceled)
        messages = self.contract_test.message_ids
        self.assertEqual(len(messages), 3)
        self.assertIn(
            'Contract line canceled: <strong>Line B</strong>',
            messages[0].body)

    def test_unlink_calls_cancel_before_deletion(self):
        fresh_line = self.env['contract.line'].create({
            'contract_id': self.contract_test.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100.0,
            'name': 'Test Line',
        })
        contract = fresh_line.contract_id
        fresh_line.unlink()
        self.assertFalse(
            self.env['contract.line'].search([('id', '=', fresh_line.id)]))
        self.assertIn(
            'Contract line canceled: <strong>Test Line</strong>',
            contract.message_ids[0].body)

    def test_unlink_with_predecessor(self):
        line_successor = self.env['contract.line'].create({
            'contract_id': self.contract_test.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 150.0,
            'name': 'Successor Line',
        })
        successor_start = self.line_test_end + relativedelta(months=1)
        line_successor.write({
            'date_start': successor_start,
            'date_end': successor_start + relativedelta(months=1),
            'recurring_next_date': successor_start,
        })
        line_successor.write({
            'predecessor_contract_line_id': self.line_test.id
        })
        self.line_test.write({
            'date_end': successor_start - relativedelta(days=1),
            'successor_contract_line_id': line_successor.id,
        })
        line_successor.unlink()
        self.assertFalse(self.line_test.successor_contract_line_id)
