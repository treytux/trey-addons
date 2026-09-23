###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import Form, TransactionCase


class TestSaleOrderLineQtyKeepPrice(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 150.0,
            'standard_price': 100.0,
        })
        self.product_b = self.env['product.product'].create({
            'name': 'Product B',
            'list_price': 300.0,
            'standard_price': 200.0,
        })

    def test_price_kept_when_qty_changes(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'price_unit': 200.0,
        })
        line.write({
            'product_uom_qty': 5.0,
        })
        line.invalidate_recordset(['price_unit'])
        line._compute_price_unit()
        self.assertEqual(line.price_unit, 200.0)

    def test_price_computed_when_product_changes(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'price_unit': 200.0,
        })
        with Form(sale) as sale_form:
            with sale_form.order_line.edit(0) as line_form:
                line_form.product_id = self.product_b
        self.assertEqual(line.price_unit, 300.0)

    def test_price_zero_not_restored(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'price_unit': 0.0,
        })
        line.write({
            'product_uom_qty': 5.0,
        })
        line.invalidate_recordset(['price_unit'])
        line._compute_price_unit()
        self.assertNotEqual(line.price_unit, 0.0)

    def test_multiple_lines_independent(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        line1 = self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'price_unit': 200.0,
        })
        line2 = self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product_b.id,
            'product_uom_qty': 2.0,
            'price_unit': 350.0,
        })
        (line1 | line2).write({
            'product_uom_qty': 10.0,
        })
        (line1 | line2).invalidate_recordset(['price_unit'])
        (line1 | line2)._compute_price_unit()
        self.assertEqual(line1.price_unit, 200.0)
        self.assertEqual(line2.price_unit, 350.0)
