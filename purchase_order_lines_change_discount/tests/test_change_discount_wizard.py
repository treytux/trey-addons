###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common


class TestPurchaseDiscount(common.TransactionCase):
    def setUp(self):
        super(TestPurchaseDiscount, self).setUp()
        self.PurchaseOrder = self.env['purchase.order']
        self.PurchaseOrderLine = self.env['purchase.order.line']
        self.DiscountWizard = self.env['change.purchase.discount.wizard']
        self.Partner = self.env['res.partner'].create({'name': 'Test Supplier'})
        self.Product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
            'standard_price': 80.0,
        })

    def test_discount_application(self):
        order = self.PurchaseOrder.create({
            'partner_id': self.Partner.id,
            'order_line': [(0, 0, {
                'product_id': self.Product.id,
                'product_qty': 2.0,
                'price_unit': 50.0,
                'name': 'Test Line',
                'date_planned': fields.Datetime.now(),
                'product_uom': self.Product.uom_po_id.id,
            })]
        })
        line = order.order_line[0]
        line.discount = 10.0
        line._compute_amount()
        expected_price_unit = 50.0 * (1 - 0.10)
        expected_subtotal = expected_price_unit * 2.0
        self.assertAlmostEqual(
            line.price_subtotal, expected_subtotal, msg='Subtotal is wrong.')

    def test_discount_wizard_draft_only(self):
        order = self.PurchaseOrder.create({
            'partner_id': self.Partner.id,
            'order_line': [(0, 0, {
                'product_id': self.Product.id,
                'product_qty': 1.0,
                'price_unit': 100.0,
                'name': 'Test Line',
                'date_planned': fields.Datetime.now(),
                'product_uom': self.Product.uom_po_id.id,
            })]
        })
        order.button_confirm()
        with self.assertRaises(UserError):
            order.open_discount_wizard()

    def test_discount_wizard_applies_discount(self):
        order = self.PurchaseOrder.create({
            'partner_id': self.Partner.id,
            'order_line': [(0, 0, {
                'product_id': self.Product.id,
                'product_qty': 1.0,
                'price_unit': 100.0,
                'name': 'Test Line',
                'date_planned': fields.Datetime.now(),
                'product_uom': self.Product.uom_po_id.id,
            })]
        })
        wizard = self.DiscountWizard.with_context(active_id=order.id).create({
            'discount': 25.0
        })
        wizard.apply_discount()
        for line in order.order_line:
            self.assertEqual(line.discount, 25.0, 'Discount was not applied.')
