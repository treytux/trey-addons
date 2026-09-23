###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import TransactionCase


class TestDeliveryCarrierTrackingIntegra2(TransactionCase):

    def setUp(self):
        super().setUp()
        self.delivery_carrier = self.env['delivery.carrier'].create({
            'name': 'Test Carrier',
            'tracking_method': 'integrados',
            'product_id': self.env['product.product'].create({
                'name': 'Test Product',
            }).id,
        })
        self.template = 'https://integrados.com/tracking/%s/%s/%s'
        self.env['ir.config_parameter'].sudo().set_param(
            'delivery_carrier.tracking_link.integrados', self.template)
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'zip': '28001',
            'lang': 'en_US',
        })
        self.shipping_partner = self.env['res.partner'].create({
            'name': 'Shipping Partner',
            'zip': '08001',
            'lang': 'en_US',
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_shipping_id': self.shipping_partner.id,
        })
        self.picking = self.env['stock.picking'].create({
            'origin': 'Test Picking',
            'partner_id': self.partner.id,
            'carrier_tracking_ref': 'TRACK123',
            'location_id': self.env['stock.location'].create({
                'name': 'Test Location',
            }).id,
            'location_dest_id': self.env['stock.location'].create({
                'name': 'Test Destination'
            }).id,
            'picking_type_id': self.env['stock.picking.type'].create({
                'name': 'Test Picking Type',
                'code': 'outgoing',
                'sequence_code': 'outgoing',
            }).id,
        })
        self.picking_with_sale = self.env['stock.picking'].create({
            'origin': 'Test Picking with Sale',
            'partner_id': self.partner.id,
            'carrier_tracking_ref': 'TRACK456',
            'sale_id': self.sale_order.id,
            'location_id': self.env['stock.location'].create({
                'name': 'Test Location',
            }).id,
            'location_dest_id': self.env['stock.location'].create({
                'name': 'Test Destination',
            }).id,
            'picking_type_id': self.env['stock.picking.type'].create({
                'name': 'Test Picking Type',
                'code': 'outgoing',
                'sequence_code': 'outgoing',
            }).id,
        })

    def test_correct_url(self):
        self.expected = self.template % (
            self.picking.carrier_tracking_ref,
            self.partner.zip[:3],
            self.partner.lang.replace('_', ''))
        self.assertEqual(
            self.delivery_carrier._get_tracking_link_integrados(self.picking),
            self.expected)

    def test_no_picking(self):
        self.assertFalse(
            self.delivery_carrier._get_tracking_link_integrados(None))

    def test_no_carrier_tracking_ref(self):
        picking = self.env['stock.picking'].create({
            'origin': 'Test Picking',
            'location_id': self.env['stock.location'].create({
                'name': 'Test Location',
            }).id,
            'location_dest_id': self.env['stock.location'].create({
                'name': 'Test Destination',
            }).id,
            'picking_type_id': self.env['stock.picking.type'].create({
                'name': 'Test Picking Type',
                'code': 'outgoing',
                'sequence_code': 'outgoing',
            }).id,
        })
        self.assertFalse(
            self.delivery_carrier._get_tracking_link_integrados(picking))

    def test_no_percentage_s_template(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'delivery_carrier.tracking_link.integrados', '')
        picking = self.env['stock.picking'].create({
            'origin': 'Test Picking',
            'carrier_tracking_ref': 'TRACK123',
            'location_id': self.env['stock.location'].create({
                'name': 'Test Location',
            }).id,
            'location_dest_id': self.env['stock.location'].create({
                'name': 'Test Destination',
            }).id,
            'picking_type_id': self.env['stock.picking.type'].create({
                'name': 'Test Picking Type',
                'code': 'outgoing',
                'sequence_code': 'outgoing',
            }).id,
        })
        self.assertFalse(
            self.delivery_carrier._get_tracking_link_integrados(picking))

    def test_zip_code_from_sale_order_shipping(self):
        result = self.delivery_carrier._get_tracking_link_integrados(
            self.picking_with_sale)
        expected = self.template % (
            self.picking_with_sale.carrier_tracking_ref,
            self.shipping_partner.zip[:3],
            self.shipping_partner.lang.replace('_', ''))
        self.assertEqual(result, expected)

    def test_zip_code_fallback_to_picking_partner(self):
        result = self.delivery_carrier._get_tracking_link_integrados(
            self.picking)
        expected = self.template % (
            self.picking.carrier_tracking_ref,
            self.partner.zip[:3],
            self.partner.lang.replace('_', ''))
        self.assertEqual(result, expected)

    def test_zip_code_missing(self):
        partner_no_zip = self.env['res.partner'].create({
            'name': 'No Zip Partner',
            'lang': 'en_US',
        })
        picking = self.env['stock.picking'].create({
            'origin': 'No Zip Picking',
            'partner_id': partner_no_zip.id,
            'carrier_tracking_ref': 'TRACK789',
            'location_id': self.env['stock.location'].create({
                'name': 'Test Location',
            }).id,
            'location_dest_id': self.env['stock.location'].create({
                'name': 'Test Destination',
            }).id,
            'picking_type_id': self.env['stock.picking.type'].create({
                'name': 'Test Picking Type',
                'code': 'outgoing',
                'sequence_code': 'outgoing',
            }).id,
        })
        result = self.delivery_carrier._get_tracking_link_integrados(picking)
        expected = self.template % ('TRACK789', '', 'enUS')
        self.assertEqual(result, expected)

    def test_language_from_partner(self):
        partner_en = self.env['res.partner'].create({
            'name': 'English Partner',
            'zip': '75001',
            'lang': 'en_US',
        })
        picking = self.env['stock.picking'].create({
            'origin': 'Lang Test',
            'partner_id': partner_en.id,
            'carrier_tracking_ref': 'LANG123',
            'location_id': self.env['stock.location'].create({
                'name': 'Test Location',
            }).id,
            'location_dest_id': self.env['stock.location'].create({
                'name': 'Test Destination',
            }).id,
            'picking_type_id': self.env['stock.picking.type'].create({
                'name': 'Test Picking Type',
                'code': 'outgoing',
                'sequence_code': 'outgoing',
            }).id,
        })
        result = self.delivery_carrier._get_tracking_link_integrados(picking)
        expected = self.template % ('LANG123', '750', 'enUS')
        self.assertEqual(result, expected)

    def test_fixed_get_tracking_link_uses_integrados_only(self):
        link = self.delivery_carrier.fixed_get_tracking_link(self.picking)
        expected = self.template % (
            self.picking.carrier_tracking_ref,
            self.partner.zip[:3],
            self.partner.lang.replace('_', ''))
        self.assertEqual(link, expected)
        self.delivery_carrier.tracking_method = False
        link = self.delivery_carrier.fixed_get_tracking_link(self.picking)
        self.assertFalse(link)

    def test_base_on_rule_get_tracking_link(self):
        link = self.delivery_carrier.base_on_rule_get_tracking_link(
            self.picking)
        expected = self.template % (
            self.picking.carrier_tracking_ref,
            self.partner.zip[:3],
            self.partner.lang.replace('_', ''))
        self.assertEqual(link, expected)
        self.delivery_carrier.tracking_method = False
        link = self.delivery_carrier.base_on_rule_get_tracking_link(
            self.picking)
        self.assertFalse(link)
