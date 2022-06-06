###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestStockPickingOptionalPackageNumber(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 20,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })]
        })
        self.sale_02 = self.sale.copy()
        self.outgoing_picking_type = self.env.ref('stock.picking_type_out')
        self.internal_picking_type = self.env.ref(
            'stock.picking_type_internal')

    def test_picking_with_package_number_active(self):
        self.assertTrue(self.outgoing_picking_type.package_number_required)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(picking.picking_type_id, self.outgoing_picking_type)
        self.assertTrue(picking.picking_type_id.package_number_required)
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(len(picking.move_lines), 1)
        wizard = self.env['stock.immediate.transfer'].create({
            'pick_ids': [(4, picking.id)]
        })
        self.assertTrue(wizard.package_number_required)
        wizard.process()

    def test_picking_with_package_number_not_active(self):
        self.assertTrue(self.outgoing_picking_type.package_number_required)
        self.outgoing_picking_type.package_number_required = False
        self.assertFalse(self.outgoing_picking_type.package_number_required)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(picking.picking_type_id, self.outgoing_picking_type)
        self.assertFalse(picking.picking_type_id.package_number_required)
        picking.action_confirm()
        picking.action_assign()
        wizard = self.env['stock.immediate.transfer'].create({
            'pick_ids': [(4, picking.id)]
        })
        self.assertFalse(wizard.package_number_required)
        wizard.process()

    def test_pickings_with_same_picking_type_and_active(self):
        self.assertTrue(self.outgoing_picking_type.package_number_required)
        self.sale.action_confirm()
        self.sale_02.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        self.assertEquals(self.sale_02.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking_02 = self.sale_02.picking_ids[0]
        self.assertEquals(picking.picking_type_id, self.outgoing_picking_type)
        self.assertEquals(
            picking_02.picking_type_id, self.outgoing_picking_type)
        self.assertTrue(picking.picking_type_id.package_number_required)
        self.assertTrue(picking_02.picking_type_id.package_number_required)
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(len(picking_02.move_lines), 1)
        wizard = self.env['stock.immediate.transfer'].create({
            'pick_ids': [(4, picking.id), (4, picking_02.id)]
        })
        self.assertTrue(wizard.package_number_required)
        wizard.process()

    def test_pickings_with_same_picking_type_and_not_active(self):
        self.assertTrue(self.outgoing_picking_type.package_number_required)
        self.outgoing_picking_type.package_number_required = False
        self.assertFalse(self.outgoing_picking_type.package_number_required)
        self.sale.action_confirm()
        self.sale_02.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        self.assertEquals(self.sale_02.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking_02 = self.sale_02.picking_ids[0]
        self.assertEquals(picking.picking_type_id, self.outgoing_picking_type)
        self.assertEquals(
            picking_02.picking_type_id, self.outgoing_picking_type)
        self.assertFalse(picking.picking_type_id.package_number_required)
        self.assertFalse(picking_02.picking_type_id.package_number_required)
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(len(picking_02.move_lines), 1)
        wizard = self.env['stock.immediate.transfer'].create({
            'pick_ids': [(4, picking.id), (4, picking_02.id)]
        })
        self.assertFalse(wizard.package_number_required)
        wizard.process()

    def test_pickings_with_diferents_picking_types_active(self):
        self.assertTrue(self.internal_picking_type.package_number_required)
        self.assertTrue(self.outgoing_picking_type.package_number_required)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        stock_location = self.env.ref('stock.stock_location_stock')
        internal_picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'location_id': stock_location.id,
            'location_dest_id': stock_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        internal_picking.action_confirm()
        internal_picking.action_assign()
        self.assertNotEquals(
            internal_picking.picking_type_id, picking.picking_type_id)
        self.assertEquals(picking.picking_type_id, self.outgoing_picking_type)
        self.assertEquals(
            internal_picking.picking_type_id, self.internal_picking_type)
        self.assertTrue(picking.picking_type_id.package_number_required)
        self.assertTrue(
            internal_picking.picking_type_id.package_number_required)
        wizard = self.env['stock.immediate.transfer'].create({
            'pick_ids': [(4, picking.id), (4, internal_picking.id)]
        })
        self.assertTrue(wizard.package_number_required)
        wizard.process()

    def test_pickings_with_diferents_picking_type_not_active(self):
        self.assertTrue(self.internal_picking_type.package_number_required)
        self.assertTrue(self.outgoing_picking_type.package_number_required)
        self.outgoing_picking_type.package_number_required = False
        self.assertFalse(self.outgoing_picking_type.package_number_required)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        stock_location = self.env.ref('stock.stock_location_stock')
        internal_picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'location_id': stock_location.id,
            'location_dest_id': stock_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 1,
                })
            ]
        })
        internal_picking.action_confirm()
        internal_picking.action_assign()
        self.assertNotEquals(
            internal_picking.picking_type_id, picking.picking_type_id)
        self.assertEquals(picking.picking_type_id, self.outgoing_picking_type)
        self.assertEquals(
            internal_picking.picking_type_id, self.internal_picking_type)
        self.assertFalse(picking.picking_type_id.package_number_required)
        self.assertTrue(
            internal_picking.picking_type_id.package_number_required)
        wizard = self.env['stock.immediate.transfer'].create({
            'pick_ids': [(4, picking.id), (4, internal_picking.id)]
        })
        self.assertTrue(wizard.package_number_required)
        wizard.process()
