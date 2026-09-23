###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class TestContractInvoiceExtraLines(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Test partner 1',
        })
        self.product_quota = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Quota product',
            'standard_price': 10,
            'list_price': 35,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product 01',
            'standard_price': 1,
            'list_price': 5,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product 02',
            'standard_price': 2,
            'list_price': 10,
        })

    def create_contract(self, partner, product, qty):
        return self.env['contract.contract'].create({
            'partner_id': partner.id,
            'invoice_partner_id': partner.id,
            'name': 'Contract for %s' % partner.name,
            'contract_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'name': product.display_name,
                    'quantity': qty,
                    'uom_id': product.uom_id.id,
                    'price_unit': product.list_price,
                    'recurring_rule_type': 'monthly',
                    'recurring_interval': 1,
                }),
            ],
        })

    def test_contract_line_extra(self):
        contract = self.create_contract(self.partner_01, self.product_quota, 1)
        self.assertTrue(contract)
        self.assertEqual(contract.partner_id, self.partner_01)
        contract_lines = contract.contract_line_fixed_ids
        self.assertEqual(len(contract_lines), 1)
        self.assertEqual(contract_lines.product_id, self.product_quota)
        self.assertEqual(contract_lines.quantity, 1)
        self.assertEqual(contract_lines.price_unit, 35)
        contract.contract_line_extra_ids = [
            (0, 0, {
                'product_id': self.product_01.id,
                'quantity': 1,
                'price_unit': self.product_01.list_price,
            }),
            (0, 0, {
                'product_id': self.product_02.id,
                'quantity': 2,
                'price_unit': self.product_02.list_price,
            }),
        ]
        for line_extra in contract.contract_line_extra_ids:
            line_extra._onchange_product_id()
        self.assertFalse(contract.contract_line_extra_ids.mapped('invoice_id'))
        contract.recurring_create_invoice()
        invoice = contract._get_related_invoices()
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(invoice.invoice_line_ids), 3)
        invoice_line_quota = invoice.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 1)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice)
        self.assertTrue(invoice_line_quota.tax_ids)
        invoice_line_extra_p1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_extra_id
            and ln.product_id == self.product_01)
        self.assertEqual(len(invoice_line_extra_p1), 1)
        self.assertEqual(
            invoice_line_extra_p1.name, self.product_01.display_name)
        self.assertEqual(invoice_line_extra_p1.quantity, 1)
        self.assertEqual(invoice_line_extra_p1.price_unit, 5)
        self.assertEqual(invoice_line_extra_p1.move_id, invoice)
        self.assertTrue(invoice_line_extra_p1.tax_ids)
        invoice_line_extra_p2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_extra_id
            and ln.product_id == self.product_02)
        self.assertEqual(len(invoice_line_extra_p2), 1)
        self.assertEqual(
            invoice_line_extra_p2.name, self.product_02.display_name)
        self.assertEqual(invoice_line_extra_p2.quantity, 2)
        self.assertEqual(invoice_line_extra_p2.price_unit, 10)
        self.assertEqual(invoice_line_extra_p2.move_id, invoice)
        self.assertTrue(invoice_line_extra_p2.tax_ids)
        contract.recurring_create_invoice()
        invoices = contract._get_related_invoices()
        self.assertEqual(
            contract.contract_line_extra_ids.mapped('invoice_id'), invoice)
        self.assertEqual(len(invoices), 2)
        invoices = invoices.sorted('id')
        invoice_02 = invoices[1]
        self.assertEqual(len(invoice_02.invoice_line_ids), 1)
        invoice_line_quota = invoice_02.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 1)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice_02)
        self.assertTrue(invoice_line_quota.tax_ids)

    def test_contract_line_extra_date_to_invoice(self):
        contract = self.create_contract(self.partner_01, self.product_quota, 1)
        self.assertTrue(contract)
        self.assertEqual(contract.partner_id, self.partner_01)
        contract_lines = contract.contract_line_fixed_ids
        self.assertEqual(len(contract_lines), 1)
        self.assertEqual(contract_lines.product_id, self.product_quota)
        self.assertEqual(contract_lines.quantity, 1)
        self.assertEqual(contract_lines.price_unit, 35)
        today = datetime.now().date()
        future_date = today + timedelta(days=45)
        contract.contract_line_extra_ids = [
            (0, 0, {
                'product_id': self.product_01.id,
                'quantity': 1,
                'price_unit': self.product_01.list_price,
            }),
            (0, 0, {
                'product_id': self.product_02.id,
                'quantity': 2,
                'price_unit': self.product_02.list_price,
                'date_to_invoice': future_date,
            }),
        ]
        for line_extra in contract.contract_line_extra_ids:
            line_extra._onchange_product_id()
        self.assertFalse(contract.contract_line_extra_ids.mapped('invoice_id'))
        contract.recurring_create_invoice()
        invoice = contract._get_related_invoices()
        self.assertEqual(len(invoice), 1)
        line_extra_product_1 = contract.contract_line_extra_ids.filtered(
            lambda ln: ln.product_id == self.product_01
        )
        self.assertEqual(line_extra_product_1.invoice_id, invoice)
        line_extra_product_2 = contract.contract_line_extra_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertFalse(line_extra_product_2.invoice_id)
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        invoice_line_quota = invoice.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 1)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice)
        self.assertTrue(invoice_line_quota.tax_ids)
        invoice_line_extra_p1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_extra_id
            and ln.product_id == self.product_01)
        self.assertEqual(len(invoice_line_extra_p1), 1)
        self.assertEqual(
            invoice_line_extra_p1.name, self.product_01.display_name)
        self.assertEqual(invoice_line_extra_p1.quantity, 1)
        self.assertEqual(invoice_line_extra_p1.price_unit, 5)
        self.assertEqual(invoice_line_extra_p1.move_id, invoice)
        self.assertTrue(invoice_line_extra_p1.tax_ids)
        invoice_line_extra_p2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_extra_id
            and ln.product_id == self.product_02)
        self.assertEqual(len(invoice_line_extra_p2), 0)
        contract.recurring_next_date = today + timedelta(days=100)
        contract.recurring_create_invoice()
        invoices = contract._get_related_invoices()
        self.assertEqual(len(invoices), 2)
        invoices = invoices.sorted('id')
        invoice_02 = invoices[1]
        line_extra_product_1 = contract.contract_line_extra_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertEqual(line_extra_product_1.invoice_id, invoice)
        line_extra_product_2 = contract.contract_line_extra_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(line_extra_product_2.invoice_id, invoice_02)
        self.assertEqual(len(invoice_02.invoice_line_ids), 2)
        invoice_line_quota = invoice_02.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 1)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice_02)
        self.assertTrue(invoice_line_quota.tax_ids)
        invoice_line_extra_p2 = invoice_02.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_extra_id
            and ln.product_id == self.product_02)
        self.assertEqual(len(invoice_line_extra_p2), 1)
        self.assertEqual(
            invoice_line_extra_p2.name, self.product_02.display_name)
        self.assertEqual(invoice_line_extra_p2.quantity, 2)
        self.assertEqual(invoice_line_extra_p2.price_unit, 10)
        self.assertEqual(invoice_line_extra_p2.move_id, invoice_02)
        self.assertTrue(invoice_line_extra_p2.tax_ids)
