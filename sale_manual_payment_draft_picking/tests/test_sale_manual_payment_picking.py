###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleManualPaymentDraftPicking(TransactionCase):
    def setUp(self):
        super().setUp()
        self.customer = self.env['res.partner'].create({
            'name': 'Customer partner #1',
            'customer': True,
        })
        self.product_01 = self.env['product.product'].create({
            'name': 'Test product #1',
            'type': 'product',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
            'standard_price': 100.0,
            'list_price': 200.0,
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.customer.id,
        })
        self.so_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product_01.id,
            'name': 'Service product normal',
            'product_uom_qty': 1,
            'product_uom': self.product_01.uom_id.id,
            'price_unit': self.product_01.list_price,
        })
        self.transaction = self.sale_order._create_payment_transaction({
            'acquirer_id': self.env.ref(
                'payment.payment_acquirer_transfer').id,
        })

    def test_locked_picking(self):
        self.env.user.company_id.manual_payment_picking_state = 'unlocked'
        self.transaction._set_transaction_pending()
        self.assertEqual(self.transaction.state, 'pending')
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.picking_ids[0].state, 'confirmed')
        self.assertFalse(self.sale_order.picking_ids[0].is_locked)
        self.assertEqual(
            self.sale_order.picking_ids[0].move_lines[0].state, 'confirmed')

    def test_draft_picking(self):
        self.env.user.company_id.manual_payment_picking_state = 'draft'
        self.transaction._set_transaction_pending()
        self.assertEqual(self.transaction.state, 'pending')
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.picking_ids[0].state, 'draft')
        self.assertFalse(self.sale_order.picking_ids[0].is_locked)
        self.assertEqual(
            self.sale_order.picking_ids[0].move_lines[0].state, 'draft')
