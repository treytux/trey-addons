###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo.exceptions import ValidationError
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

    def _image_b64(self):
        with open(
            '%s/static/img/signature.png' % get_resource_path(
                'stock_picking_signature'), 'rb'
        ) as file:
            return base64.b64encode(file.read())

    def _picking_ready(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 10,
                }),
            ],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        return picking

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
            ],
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
                'signed_by': 'Signer name test',
                'signature': signature,
                'filename': 'Carrier signature test',
            })
        self.assertTrue(wizard.signature)
        self.assertEqual(wizard.filename, 'Carrier signature test')
        res = wizard.button_accept_sign()
        self.assertEqual(res['type'], 'ir.actions.act_window_close')
        picking_attachment_sign = self.env['ir.attachment'].search([
            ('res_model', '=', 'stock.picking'),
            ('res_id', '=', picking.id),
            ('name', '=', 'Carrier signature test'),
        ])
        self.assertEqual(len(picking_attachment_sign), 1)
        picking_attachment = picking_attachment_sign
        self.assertTrue(picking.signature)
        self.assertTrue(picking.signature_datetime)
        self.assertEqual(picking.signed_by, 'Signer name test')
        self.assertEqual(picking.signature_filename, 'Carrier signature test')
        self.assertEqual(picking_attachment.name, 'Carrier signature test')
        self.assertTrue(picking_attachment.datas)
        self.assertEqual(picking_attachment.res_model, 'stock.picking')
        self.assertEqual(picking_attachment.res_id, picking.id)

    def test_wizard_photo_mode_stores_proof_and_attachment(self):
        picking = self._picking_ready()
        image = self._image_b64()
        wizard = self.env['wizard.stock.picking.signature'].with_context(
            active_id=picking.id).create({
                'capture_mode': 'photo',
                'signed_by': 'Warehouse operator',
                'proof_image': image,
                'filename': 'albaran_sellado.jpg',
            })
        wizard.button_accept_sign()
        self.assertTrue(picking.delivery_proof_image)
        self.assertEqual(
            picking.delivery_proof_filename, 'albaran_sellado.jpg')
        self.assertEqual(picking.signed_by, 'Warehouse operator')
        self.assertTrue(picking.signature_datetime)
        self.assertFalse(picking.signature)
        attachment = picking.delivery_proof_attachment_id
        self.assertTrue(attachment)
        self.assertEqual(attachment.res_model, 'stock.picking')
        self.assertEqual(attachment.res_id, picking.id)
        self.assertTrue(attachment.datas)

    def test_wizard_photo_mode_marks_picking_signed(self):
        picking = self._picking_ready()
        self.assertFalse(picking.is_signed)
        wizard = self.env['wizard.stock.picking.signature'].with_context(
            active_id=picking.id).create({
                'capture_mode': 'photo',
                'signed_by': 'Warehouse operator',
                'proof_image': self._image_b64(),
            })
        wizard.button_accept_sign()
        self.assertTrue(picking.is_signed)

    def test_wizard_sign_mode_requires_signature(self):
        picking = self._picking_ready()
        with self.assertRaises(ValidationError):
            self.env['wizard.stock.picking.signature'].with_context(
                active_id=picking.id).create({
                    'capture_mode': 'sign',
                    'signed_by': 'Signer',
                    'filename': 'signature.png',
                })

    def test_wizard_photo_mode_requires_photo(self):
        picking = self._picking_ready()
        with self.assertRaises(ValidationError):
            self.env['wizard.stock.picking.signature'].with_context(
                active_id=picking.id).create({
                    'capture_mode': 'photo',
                    'signed_by': 'Signer',
                })
