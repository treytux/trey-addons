###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo.modules.module import get_resource_path
from odoo.tests import common


class TestStockPickingSignature(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'list_price': 30,
        })

    def test_agreement_acceptance(self):
        with open(
            '%s/static/img/signature.png' % get_resource_path(
                'stock_picking_signature'),
            'rb'
        ) as file:
            signature = base64.b64encode(file.read())
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 10,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.signature)
        self.assertFalse(picking.signature_datetime)
        self.assertFalse(picking.signature_filename)
        wizard = self.env['wizard.stock.picking.signature'].with_context(
            active_id=picking.id).create({
                'signature': signature,
                'filename': 'Carrier signature test',
            })
        self.assertTrue(wizard.signature)
        self.assertEqual(wizard.filename, 'Carrier signature test')
        picking_attachments_01 = self.env['ir.attachment'].search([
            ('res_model', '=', 'stock.picking'),
            ('res_id', '=', picking.id),
        ])
        res = wizard.button_accept_sign()
        self.assertEqual(res['type'], 'ir.actions.act_window_close')
        picking_attachments_02 = self.env['ir.attachment'].search([
            ('res_model', '=', 'stock.picking'),
            ('res_id', '=', picking.id),
        ])
        self.assertNotEqual(
            len(picking_attachments_01), len(picking_attachments_02))
        self.assertEqual(
            len(picking_attachments_01) + 1, len(picking_attachments_02))
        self.assertEqual(len(picking_attachments_02), 1)
        picking_attachment = picking_attachments_02
        self.assertTrue(picking.signature)
        self.assertTrue(picking.signature_datetime)
        self.assertEqual(picking.signature_filename, 'Carrier signature test')
        self.assertEqual(picking.signature_filename, wizard.filename)
        self.assertEqual(picking_attachment.name, 'Carrier signature test')
        self.assertEqual(picking_attachment.name, wizard.filename)
        self.assertEqual(picking_attachment.datas_fname, wizard.filename)
        self.assertTrue(picking_attachment.datas)
        self.assertEqual(picking_attachment.res_model, 'stock.picking')
        self.assertEqual(picking_attachment.res_id, picking.id)
