###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleForceInvoiceFinancialRisk(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100,
        })
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.line = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'price_unit': 100,
        })

    def test_risk_amount_force_invoiced(self):
        self.order.force_invoiced = True
        self.order.action_confirm()
        self.line._compute_risk_amount()
        self.assertEqual(self.line.risk_amount, 0.0)

    def test_risk_amount_normal(self):
        self.order.force_invoiced = False
        self.order.action_confirm()
        self.line._compute_risk_amount()
        self.assertGreater(self.line.risk_amount, 0.0)
