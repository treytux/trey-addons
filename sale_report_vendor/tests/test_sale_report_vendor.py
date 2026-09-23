###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleReportVendor(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test customer',
        })
        self.vendor_a = self.env['res.partner'].create({
            'name': 'Vendor A',
        })
        self.vendor_b = self.env['res.partner'].create({
            'name': 'Vendor B',
        })
        self.product_with_vendor = self.env['product.product'].create({
            'name': 'Product with vendor',
        })
        self.env['product.supplierinfo'].create({
            'partner_id': self.vendor_a.id,
            'product_tmpl_id': self.product_with_vendor.product_tmpl_id.id,
        })
        self.product_no_vendor = self.env['product.product'].create({
            'name': 'Product no vendor',
        })

    def test_onchange_product_sets_vendor(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line = self.env['sale.order.line'].new({
            'order_id': sale.id,
            'product_id': self.product_with_vendor.id,
            'product_uom_qty': 1,
            'product_uom': self.product_with_vendor.uom_id.id,
        })
        line.product_id_change()
        self.assertTrue(line.vendor_id)
        self.assertEqual(line.vendor_id, self.vendor_a)

    def test_onchange_product_no_seller_clears_vendor(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line = self.env['sale.order.line'].new({
            'order_id': sale.id,
            'product_id': self.product_no_vendor.id,
            'product_uom_qty': 1,
            'product_uom': self.product_no_vendor.uom_id.id,
        })
        line.product_id_change()
        self.assertFalse(line.vendor_id)

    def test_sale_report_exposes_vendor(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product_with_vendor.id,
            'product_uom_qty': 1,
            'product_uom': self.product_with_vendor.uom_id.id,
            'vendor_id': self.vendor_a.id,
        })
        sale.action_confirm()
        report = self.env['sale.report'].search([
            ('order_id', '=', sale.id),
        ])
        self.assertTrue(report)
        self.assertEqual(report.vendor_id, self.vendor_a)

    def test_sale_report_group_by_vendor(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product_with_vendor.id,
            'product_uom_qty': 2,
            'product_uom': self.product_with_vendor.uom_id.id,
            'vendor_id': self.vendor_a.id,
        })
        self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product_with_vendor.id,
            'product_uom_qty': 3,
            'product_uom': self.product_with_vendor.uom_id.id,
            'vendor_id': self.vendor_b.id,
        })
        sale.action_confirm()
        grouped = self.env['sale.report'].read_group(
            [('order_id', '=', sale.id)],
            ['product_uom_qty', 'vendor_id'],
            ['vendor_id'],)
        vendors = {g['vendor_id'][0] for g in grouped if g['vendor_id']}
        self.assertIn(self.vendor_a.id, vendors)
        self.assertIn(self.vendor_b.id, vendors)
