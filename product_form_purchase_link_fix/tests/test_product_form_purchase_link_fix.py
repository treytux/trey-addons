###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestProductPurchaseLinkFix(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner'
        })
        self.attribute = self.env['product.attribute'].create({
            'name': 'Size'
        })
        self.val_s = self.env['product.attribute.value'].create({
            'name': 'S',
            'attribute_id': self.attribute.id,
        })
        self.val_m = self.env['product.attribute.value'].create({
            'name': 'M',
            'attribute_id': self.attribute.id
        })
        self.product_tmpl = self.env['product.template'].create({
            'name': 'Test Shirt',
            'purchase_ok': True,
            'detailed_type': 'consu',
            'attribute_line_ids': [(0, 0, {
                'attribute_id': self.attribute.id,
                'value_ids': [(6, 0, [self.val_s.id, self.val_m.id])]
            })]
        })
        self.variant_1 = self.product_tmpl.product_variant_ids[0]
        self.variant_2 = self.product_tmpl.product_variant_ids[1]

    def test_action_view_po_variant_domain(self):
        action = self.variant_1.action_view_po()
        domain = action.get('domain', [])
        self.assertIn(('product_id', 'in', self.variant_1.ids), domain)

    def test_action_view_po_template_domain(self):
        action = self.product_tmpl.action_view_po()
        domain = action.get('domain', [])
        self.assertIn((
            'product_id', 'in', self.product_tmpl.product_variant_ids.ids),
            domain)

    def test_compute_qty_within_365_days(self):
        self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'date_order': fields.Datetime.now(),
            'order_line': [
                (0, 0, {
                    'product_id': self.variant_1.id,
                    'product_qty': 10.0,
                    'price_unit': 1.0,
                })],
        })
        self.variant_1.invalidate_recordset(['purchased_product_qty'])
        self.assertEqual(self.variant_1.purchased_product_qty, 10.0)

    def test_compute_qty_outside_365_days(self):
        date_old = fields.Datetime.now() - timedelta(days=400)
        self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'date_order': date_old,
            'order_line': [
                (0, 0, {
                    'product_id': self.variant_1.id,
                    'product_qty': 50.0,
                    'price_unit': 1.0,
                })],
        })
        self.variant_1.invalidate_recordset(['purchased_product_qty'])
        self.assertEqual(self.variant_1.purchased_product_qty, 0.0)

    def test_compute_qty_includes_draft_and_confirmed(self):
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'date_order': fields.Datetime.now(),
            'order_line': [
                (0, 0, {
                    'product_id': self.variant_1.id,
                    'product_qty': 5.0,
                    'price_unit': 1.0,
                })],
        })
        self.variant_1.invalidate_recordset(['purchased_product_qty'])
        self.assertEqual(self.variant_1.purchased_product_qty, 5.0)
        po.button_confirm()
        self.variant_1.invalidate_recordset(['purchased_product_qty'])
        self.assertEqual(self.variant_1.purchased_product_qty, 5.0)

    def test_date_approve_behavior(self):
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'date_order': fields.Datetime.now(),
            'order_line': [
                (0, 0, {
                    'product_id': self.variant_1.id,
                    'product_qty': 1.0,
                    'price_unit': 1.0,
                })],
        })
        self.assertFalse(po.date_approve)
        po.button_confirm()
        self.assertTrue(po.date_approve)
        self.variant_1.invalidate_recordset(['purchased_product_qty'])
        self.assertEqual(self.variant_1.purchased_product_qty, 1.0)
