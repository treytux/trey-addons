###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestDeliveryCarrierManifestSignature(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'type': 'product',
            'default_code': 'PR-TEST',
            'standard_price': 10,
            'list_price': 35,
        })
        self.product_delivery = self.env['product.product'].create({
            'type': 'service',
            'name': 'Service delivery test',
            'standard_price': 2.99,
            'list_price': 2.99,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'delivery_type': 'fixed',
            'product_id': self.product_delivery.id,
            'fixed_price': 2.99,
        })
        self.sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 45,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.sale_02 = self.sale_01.copy()
        self.sale_01.action_confirm()
        self.sale_02.action_confirm()

    def test_sign_delivery_carrier_manifest(self):
        self.assertEqual(len(self.sale_01.picking_ids), 1)
        self.assertEqual(len(self.sale_02.picking_ids), 1)
        picking_01 = self.sale_01.picking_ids[0]
        picking_02 = self.sale_02.picking_ids[0]
        self.assertTrue(picking_01.carrier_id)
        self.assertTrue(picking_02.carrier_id)
        self.assertEqual(picking_01.carrier_id, picking_02.carrier_id)
        self.assertFalse(picking_01.manifest_id.exists())
        self.assertFalse(picking_02.manifest_id.exists())
        wizard = self.env['picking.manifest.report'].with_context({
            'active_ids': [picking_01.id, picking_02.id],
        }).create({})
        wizard.button_print()
        self.assertTrue(picking_01.manifest_id.exists())
        self.assertTrue(picking_02.manifest_id.exists())
        self.assertEqual(picking_01.manifest_id.id, picking_02.manifest_id.id)
        wizard = self.env['delivery.carrier.manifest.signature'].with_context({
            'active_id': picking_01.manifest_id.id,
        }).create({
            'signature': 'signature.pdf',
        })
        manifest_01 = picking_01.manifest_id
        self.assertFalse(manifest_01.signature)
        self.assertFalse(manifest_01.is_signed)
        self.assertFalse(manifest_01.signature_date)
        attachment = self.env['ir.attachment'].search([
            ('res_id', '=', manifest_01.id),
            ('res_model', '=', 'delivery.carrier.manifest'),
        ])
        self.assertEqual(len(attachment), 0)
        for picking in manifest_01.picking_ids:
            attachment = self.env['ir.attachment'].search([
                ('res_id', '=', picking.id),
                ('res_model', '=', 'stock.picking'),
            ])
            self.assertEqual(len(attachment), 0)
            self.assertFalse(picking.signature)
            self.assertFalse(picking.signature_date)
        wizard.button_sign_manifest()
        self.assertTrue(manifest_01.signature)
        attachment = self.env['ir.attachment'].search([
            ('res_id', '=', manifest_01.id),
            ('res_model', '=', 'delivery.carrier.manifest'),
        ])
        self.assertEqual(len(attachment), 1)
        self.assertTrue(manifest_01.signature)
        self.assertTrue(manifest_01.signature_date)
        self.assertTrue(manifest_01.is_signed)
        for picking in manifest_01.picking_ids:
            attachment = self.env['ir.attachment'].search([
                ('res_id', '=', picking.id),
                ('res_model', '=', 'stock.picking'),
            ])
            self.assertEqual(len(attachment), 1)
            self.assertTrue(picking.signature)
            self.assertTrue(picking.signature_date)
