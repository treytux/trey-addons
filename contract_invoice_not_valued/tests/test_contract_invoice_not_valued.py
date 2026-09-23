###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestContractInvoiceNotValued(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.product = cls.env.ref('product.product_product_4')
        cls.contract = cls.env['contract.contract'].create({
            'name': 'Test Contract',
            'partner_id': cls.partner.id,
            'recurring_rule_type': 'monthly',
            'recurring_interval': 1,
            'date_start': fields.Date.today(),
            'contract_line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'quantity': 1,
                'price_unit': 100.0,
                'name': 'Test Line',
            })],
        })

    def test_field_default(self):
        self.assertTrue(self.contract.show_valued_lines)

    def test_prepare_recurring_invoices_values(self):
        vals = self.contract._prepare_recurring_invoices_values()
        self.assertTrue(len(vals) > 0)
        for invoice_vals in vals:
            self.assertTrue(invoice_vals.get('show_valued_lines'))
        self.contract.show_valued_lines = False
        vals = self.contract._prepare_recurring_invoices_values()
        for invoice_vals in vals:
            self.assertFalse(invoice_vals.get('show_valued_lines'))

    def test_prepare_with_no_lines(self):
        contract_no_lines = self.env['contract.contract'].create({
            'name': 'No Lines',
            'partner_id': self.partner.id,
            'recurring_rule_type': 'monthly',
            'recurring_interval': 1,
            'date_start': fields.Date.today(),
        })
        vals = contract_no_lines._prepare_recurring_invoices_values()
        self.assertEqual(vals, [])
