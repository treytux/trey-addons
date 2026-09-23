###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import logging

from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestPortalStockPickingSignature(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 30,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 10,
                }),
            ],
        })
        self.sale.action_confirm()
        self.picking = self.sale.picking_ids[0]

    def _validate_picking(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        for move in self.picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        self.picking._action_done()

    def test_sign_button_requires_done_and_sale_id(self):
        view = self.env.ref('portal_stock_picking_signature.view_picking_form')
        self.assertIn('call_signature_portal_from_picking', view.arch)
        self.assertIn("'state', '!=', 'done'", view.arch)
        self.assertIn("'sale_id', '=', False", view.arch)

    def test_sign_flow_from_backend_button(self):
        self._validate_picking()
        self.assertEqual(self.picking.state, 'done')
        self.assertTrue(self.picking.sale_id)
        self.assertEqual(self.picking.pending_signed, 'not_signed')
        action = self.picking.call_signature_portal_from_picking()
        self.assertEqual(self.picking.pending_signed, 'pending')
        self.assertEqual(
            action['tag'],
            'portal_stock_picking_signature.picking_signature_sale_session')
        picking_ctx = self.picking.with_context(picking=self.picking.id)
        self.assertEqual(
            picking_ctx.get_pending_picking_sign_portal(), 'pending')
        self.picking.write({
            'signature': base64.b64encode(b'test signature'),
            'signed_by': 'Test signer',
            'pending_signed': 'signed',
        })
        self.assertTrue(self.picking.is_signed)
        self.assertEqual(
            picking_ctx.get_pending_picking_sign_portal(), 'signed')
        report_action = picking_ctx.print_picking_report_sale_session()
        self.assertEqual(report_action['type'], 'ir.actions.report')

    def test_sign_cancel_flow(self):
        self._validate_picking()
        self.picking.call_signature_portal_from_picking()
        picking_ctx = self.picking.with_context(picking=self.picking.id)
        picking_ctx.set_cancel_pending_picking()
        self.assertEqual(self.picking.pending_signed, 'cancel')
        self.assertEqual(
            picking_ctx.get_pending_picking_sign_portal(), 'cancel')

    def test_portal_search_only_finds_done_pickings_pending_sign(self):
        self._validate_picking()
        self.picking.call_signature_portal_from_picking()
        domain = [
            ('sale_id', '=', self.sale.id),
            ('state', '=', 'done'),
            ('pending_signed', '=', 'pending'),
        ]
        found = self.env['stock.picking'].search(domain, limit=1)
        self.assertEqual(found, self.picking)

    def test_access_url_matches_controller_route(self):
        self.assertEqual(
            self.picking.access_url,
            '/my/pending_picking/%s' % self.picking.id)
