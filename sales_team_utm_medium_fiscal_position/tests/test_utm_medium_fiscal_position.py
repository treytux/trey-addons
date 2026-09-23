###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestUtmMediumFiscalPosition(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.account_receivable = self.env['account.account'].create({
            'code': 'RCVTEST430',
            'name': 'Test Account Receivable',
            'account_type': 'asset_receivable',
            'reconcile': True,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'property_account_receivable_id': self.account_receivable.id,
        })
        self.account_700000 = self.env['account.account'].create({
            'code': 'INCTEST700000',
            'name': 'Test Income Account 700000',
            'account_type': 'income',
        })
        self.account_700001 = self.env['account.account'].create({
            'code': 'INCTEST700001',
            'name': 'Test Income Account 700001',
            'account_type': 'income',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
            'standard_price': 50.0,
            'property_account_income_id': self.account_700000.id,
        })
        self.utm_medium = self.env['utm.medium'].create({
            'name': 'Web ecommerce',
        })
        self.fiscal_position = self.env['account.fiscal.position'].create({
            'name': 'Test Fiscal Position',
            'account_ids': [(0, 0, {
                'account_src_id': self.account_700000.id,
                'account_dest_id': self.account_700001.id,
                'medium_id': self.utm_medium.id,
            })],
        })

    def _create_invoice(self, medium=None, fiscal_position=None):
        return self.env['account.move'].create({
            'partner_id': self.partner.id,
            'medium_id': medium.id if medium else False,
            'fiscal_position_id': (
                fiscal_position.id if fiscal_position else False
            ),
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })

    def test_fiscal_position_account_medium_field(self):
        account_mapping = self.fiscal_position.account_ids[0]
        self.assertEqual(
            account_mapping.medium_id.id, self.utm_medium.id)
        new_medium = self.env['utm.medium'].create({
            'name': 'New Medium',
        })
        account_mapping.write({
            'medium_id': new_medium.id,
        })
        self.assertEqual(account_mapping.medium_id.id, new_medium.id)

    def test_fiscal_position_without_medium_on_mapping(self):
        account_mapping = self.fiscal_position.account_ids[0]
        account_mapping.write({'medium_id': False})
        self.assertFalse(account_mapping.medium_id)

    def test_invoice_line_account_mapping_with_medium(self):
        invoice = self._create_invoice(
            self.utm_medium, self.fiscal_position)
        line = self.env['account.move.line'].with_context(
            check_move_validity=False
        ).create({
            'move_id': invoice.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100.0,
            'account_id': self.account_700000.id,
        })
        line._onchange_product_id()
        self.assertEqual(line.account_id.id, self.account_700001.id)

    def test_invoice_line_account_without_medium(self):
        invoice = self._create_invoice(
            fiscal_position=self.fiscal_position)
        line = self.env['account.move.line'].with_context(
            check_move_validity=False
        ).create({
            'move_id': invoice.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100.0,
            'account_id': self.account_700000.id,
        })
        line._onchange_product_id()
        self.assertEqual(line.account_id.id, self.account_700000.id)

    def test_invoice_line_account_without_fiscal_position(self):
        invoice = self._create_invoice(medium=self.utm_medium)
        line = self.env['account.move.line'].with_context(
            check_move_validity=False
        ).create({
            'move_id': invoice.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100.0,
            'account_id': self.account_700000.id,
        })
        line._onchange_product_id()
        self.assertEqual(line.account_id.id, self.account_700000.id)

    def test_invoice_line_account_different_medium(self):
        other_medium = self.env['utm.medium'].create({
            'name': 'Other Medium',
        })
        invoice = self._create_invoice(
            other_medium, self.fiscal_position)
        line = self.env['account.move.line'].with_context(
            check_move_validity=False
        ).create({
            'move_id': invoice.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100.0,
            'account_id': self.account_700000.id,
        })
        line._onchange_product_id()
        self.assertEqual(line.account_id.id, self.account_700000.id)

    def test_multiple_account_mappings(self):
        account_800000 = self.env['account.account'].create({
            'code': '800000',
            'name': 'Income Account 800000',
            'account_type': 'income',
        })
        account_800001 = self.env['account.account'].create({
            'code': '800001',
            'name': 'Income Account 800001',
            'account_type': 'income',
        })
        self.fiscal_position.write({
            'account_ids': [(0, 0, {
                'account_src_id': account_800000.id,
                'account_dest_id': account_800001.id,
                'medium_id': self.utm_medium.id,
            })],
        })
        invoice = self._create_invoice(
            self.utm_medium, self.fiscal_position)
        line1 = self.env['account.move.line'].with_context(
            check_move_validity=False
        ).create({
            'move_id': invoice.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100.0,
            'account_id': self.account_700000.id,
        })
        line1._onchange_product_id()
        self.assertEqual(line1.account_id.id, self.account_700001.id)
        line2 = self.env['account.move.line'].with_context(
            check_move_validity=False
        ).create({
            'move_id': invoice.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100.0,
            'account_id': account_800000.id,
        })
        line2._onchange_product_id()
        self.assertEqual(line2.account_id.id, account_800001.id)

    def test_fiscal_position_mapping_without_medium(self):
        fp_no_medium = self.env['account.fiscal.position'].create({
            'name': 'FP Without Medium on Mapping',
            'account_ids': [(0, 0, {
                'account_src_id': self.account_700000.id,
                'account_dest_id': self.account_700001.id,
            })],
        })
        account_mapping = fp_no_medium.account_ids[0]
        self.assertFalse(account_mapping.medium_id)
        invoice = self._create_invoice(self.utm_medium, fp_no_medium)
        line = self.env['account.move.line'].with_context(
            check_move_validity=False
        ).create({
            'move_id': invoice.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100.0,
            'account_id': self.account_700000.id,
        })
        line._onchange_product_id()
        self.assertEqual(line.account_id.id, self.account_700000.id)
