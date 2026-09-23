###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestDeliveryCarrierManifest(TransactionCase):

    def setUp(self):
        super().setUp()
        self.outgoing_picking_type = self.env.ref('stock.picking_type_out')
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.tax_21 = self.env['account.tax'].create({
            'name': '21%',
            'amount_type': 'percent',
            'amount': 21,
            'type_tax_use': 'sale',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'name': 'Test product',
        })
        self.product_carrier_01 = self.env['product.product'].create({
            'name': 'Carrier product 01',
            'default_code': 'CP01',
            'taxes_id': [(6, 0, self.tax_21.ids)],
        })
        self.product_carrier_02 = self.env['product.product'].create({
            'name': 'Carrier product 02',
            'default_code': 'CP02',
            'taxes_id': [(6, 0, self.tax_21.ids)],
        })
        self.carrier_01 = self.env['delivery.carrier'].create({
            'name': 'Carrier 01',
            'delivery_type': 'fixed',
            'product_id': self.product_carrier_01.id,
        })
        self.carrier_02 = self.env['delivery.carrier'].create({
            'name': 'Carrier 02',
            'delivery_type': 'fixed',
            'product_id': self.product_carrier_02.id,
        })
        self.manifest_test = self.env['delivery.carrier.manifest'].create({
            'name': 'MANIF000001',
            'carrier_id': self.carrier_02.id,
        })
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        warehouse = self.env.ref('stock.warehouse0')
        customer_loc = self.env.ref('stock.stock_location_customers')
        self.picking_01 = self.env['stock.picking'].create({
            'partner_id': partner.id,
            'picking_type_id': warehouse.out_type_id.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'location_dest_id': customer_loc.id,
            'carrier_id': self.carrier_01.id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.picking_02 = self.env['stock.picking'].create({
            'partner_id': partner.id,
            'picking_type_id': warehouse.out_type_id.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'location_dest_id': customer_loc.id,
            'carrier_id': self.carrier_01.id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.picking_03 = self.env['stock.picking'].create({
            'partner_id': partner.id,
            'picking_type_id': warehouse.out_type_id.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'location_dest_id': customer_loc.id,
            'carrier_id': self.carrier_02.id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 1,
                }),
            ],
        })

    def test_get_manifests_error(self):
        self.picking_02.write({
            'carrier_id': False,
        })
        self.assertEquals(self.picking_02.carrier_id.id, False)
        wizard = self.env['picking.manifest.report'].with_context({
            'active_ids': [
                self.picking_01.id, self.picking_02.id, self.picking_03.id],
        }).create({})
        with self.assertRaises(Exception):
            wizard.button_print()
        self.picking_02.write({
            'carrier_id': self.carrier_01.id,
            'manifest_id': self.manifest_test.id,
        })
        self.assertEquals(self.picking_02.manifest_id, self.manifest_test)
        with self.assertRaises(Exception):
            wizard.button_print()

    def test_get_manifests(self):
        self.assertEquals(self.picking_02.carrier_id.id, self.carrier_01.id)
        self.assertFalse(self.picking_02.manifest_id.exists())
        wizard = self.env['picking.manifest.report'].with_context({
            'active_ids': [
                self.picking_01.id, self.picking_02.id, self.picking_03.id],
        }).create({})
        wizard.button_print()
        self.assertTrue(self.picking_01.manifest_id.exists())
        self.assertEquals(
            self.picking_02.manifest_id.id, self.picking_01.manifest_id.id)
        self.assertTrue(self.picking_03.manifest_id.exists())
