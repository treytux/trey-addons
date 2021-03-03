# Copyright 2019 Vicent Cubells - Trey <http://www.trey.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestPurchaseOrder(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestPurchaseOrder, cls).setUpClass()
        cls.supplierinfo_obj = cls.env['product.supplierinfo']
        cls.partner = cls.env['res.partner'].create({
            'name': 'Partner #1',
        })
        cls.partner2 = cls.env['res.partner'].create({
            'name': 'Partner #2',
        })
        cls.product1 = cls.env['product.product'].create({
            'name': 'Test Product 1',
            'purchase_method': 'purchase',
        })
        cls.product2 = cls.env['product.product'].create({
            'name': 'Test Product 2',
            'purchase_method': 'purchase',
        })
        cls.supplierinfo = cls.supplierinfo_obj.create({
            'min_qty': 0.0,
            'name': cls.partner2.id,
            'product_tmpl_id': cls.product1.product_tmpl_id.id,
            'multiple_discount': '20+10',
            'price': 100,
        })
        cls.tax = cls.env['account.tax'].create({
            'name': 'TAX 15%',
            'amount_type': 'percent',
            'type_tax_use': 'purchase',
            'amount': 15.0,
        })
        cls.order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.order2 = cls.env['purchase.order'].create({
            'partner_id': cls.partner2.id,
        })
        po_line = cls.env['purchase.order.line']
        cls.po_line1 = po_line.create({
            'order_id': cls.order.id,
            'product_id': cls.product1.id,
            'date_planned': '2018-01-19 00:00:00',
            'name': 'Line 1',
            'product_qty': 1.0,
            'product_uom': cls.product1.uom_id.id,
            'taxes_id': [(6, 0, [cls.tax.id])],
            'price_unit': 600.0,
        })
        cls.po_line2 = po_line.create({
            'order_id': cls.order.id,
            'product_id': cls.product2.id,
            'date_planned': '2018-01-19 00:00:00',
            'name': 'Line 2',
            'product_qty': 10.0,
            'product_uom': cls.product2.uom_id.id,
            'taxes_id': [(6, 0, [cls.tax.id])],
            'price_unit': 60.0,
        })
        cls.po_line3 = po_line.create({
            'order_id': cls.order2.id,
            'product_id': cls.product1.id,
            'date_planned': '2020-01-01 00:00:00',
            'name': 'Line 1',
            'product_qty': 1.0,
            'product_uom': cls.product1.uom_id.id,
            'taxes_id': [(6, 0, [cls.tax.id])],
            'price_unit': 600.0,
        })

    def test_purchase_order_classic_discount(self):
        """ Tests with single discount """
        self.po_line1.discount = 50.0
        self.po_line2.discount = 75.0
        self.assertEqual(self.po_line1.price_subtotal, 300.0)
        self.assertEqual(self.po_line2.price_subtotal, 150.0)
        self.assertEqual(self.order.amount_untaxed, 450.0)
        self.assertEqual(self.order.amount_tax, 67.5)
        # Mix taxed and untaxed:
        self.po_line1.taxes_id = False
        self.assertEqual(self.order.amount_tax, 22.5)

    def test_purchase_order_simple_multiple_discount(self):
        """ Tests on a single line """
        self.po_line2.unlink()
        self.po_line1.multiple_discount = '30+5'
        self.assertEqual(self.po_line1.price_subtotal, 399.0)
        self.assertEqual(self.order.amount_untaxed, 399.0)
        self.assertEqual(self.order.amount_tax, 59.85)
        self.po_line1.multiple_discount = ''
        self.assertEqual(self.po_line1.price_subtotal, 600.0)
        self.assertEqual(self.order.amount_untaxed, 600.0)
        self.assertEqual(self.order.amount_tax, 90.0)
        # Set a charge instead:
        self.po_line1.multiple_discount = '-30-5'
        self.assertEqual(self.po_line1.price_subtotal, 819.0)
        self.assertEqual(self.order.amount_untaxed, 819.0)
        self.assertEqual(self.order.amount_tax, 122.85)

    def test_purchase_order_complex_multiple_discount(self):
        """ Tests on multiple lines """
        self.po_line1.multiple_discount = '40+10'
        self.assertEqual(self.po_line1.price_subtotal, 324.0)
        self.assertEqual(self.order.amount_untaxed, 924.0)
        self.assertEqual(self.order.amount_tax, 138.6)
        self.po_line2.multiple_discount = '10+5'
        self.assertEqual(self.po_line2.price_subtotal, 513.0)
        self.assertEqual(self.order.amount_untaxed, 837.0)
        self.assertEqual(self.order.amount_tax, 125.55)

    def test_purchase_order_multiple_discount_invoicing(self):
        """ When a confirmed order is invoiced, the resultant invoice
            should inherit the discounts """
        self.po_line1.multiple_discount = '50+25'
        self.po_line2.multiple_discount = '40+10'
        self.order.button_confirm()
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'purchase_id': self.order.id,
            'account_id': self.partner.property_account_payable_id.id,
            'type': 'in_invoice',
        })
        self.invoice.purchase_order_change()
        self.invoice._onchange_invoice_line_ids()
        self.assertEqual(self.po_line1.multiple_discount,
                         self.invoice.invoice_line_ids[0].multiple_discount)
        self.assertEqual(self.po_line2.multiple_discount,
                         self.invoice.invoice_line_ids[1].multiple_discount)
        self.assertEqual(self.order.amount_total, self.invoice.amount_total)

    def test_purchase_order_default_discount(self):
        self.po_line3._onchange_quantity()
        self.assertEquals(self.po_line3.multiple_discount, '20+10')

    def test_default_supplier_discount(self):
        self.partner2.default_supplierinfo_multiple_discount = '10+5'
        supplierinfo = self.supplierinfo_obj.new({
            'min_qty': 0.0,
            'name': self.partner2.id,
            'product_tmpl_id': self.product1.product_tmpl_id.id,
            'multiple_discount': '20+10',
        })
        supplierinfo.onchange_name()
        self.assertEquals(supplierinfo.multiple_discount, '10+5')

    def test_supplierinfo_from_purchaseorder(self):
        self.order2.order_line.create({
            'order_id': self.order2.id,
            'product_id': self.product2.id,
            'date_planned': '2020-01-01 00:00:00',
            'name': 'Line 2',
            'product_qty': 1.0,
            'product_uom': self.product2.uom_id.id,
            'taxes_id': [(6, 0, [self.tax.id])],
            'price_unit': 999.0,
            'multiple_discount': '10+5',
        })
        self.order2.button_confirm()
        seller = self.supplierinfo_obj.search([
            ('name', '=', self.partner2.id),
            ('product_tmpl_id', '=', self.product2.product_tmpl_id.id)])
        self.assertTrue(seller)
        self.assertEqual(seller.multiple_discount, '10+5')

    def test_purchase_order_with_lines_no_saved(self):
        order1 = self.env['purchase.order'].create({
            'partner_id': self.partner2.id,
        })
        po_line = self.env['purchase.order.line'].new({
            'order_id': order1.id,
            'product_id': self.product1.id,
            'date_planned': '2021-01-19 00:00:00',
            'name': 'Line 1',
            'product_qty': 1.0,
            'product_uom': self.product1.uom_id.id,
            'taxes_id': [(6, 0, [self.tax.id])],
            'price_unit': 1.0,
        })
        po_line.onchange_product_id()
        po_line.onchange_multiple_discount()
        self.assertEquals(po_line.product_qty, 1)
        self.assertEquals(po_line.price_unit, 100)
        self.assertEquals(po_line.multiple_discount, '20+10')
        self.assertEquals(po_line.discount, 28)
        self.assertEquals(po_line.price_subtotal, 72)
        po_line.product_qty = 10
        po_line._onchange_quantity()
        po_line.onchange_multiple_discount()
        self.assertEquals(po_line.product_qty, 10)
        self.assertEquals(po_line.price_unit, 100)
        self.assertEquals(po_line.multiple_discount, '20+10')
        self.assertEquals(po_line.discount, 28)
        self.assertEquals(po_line.price_subtotal, 720)
