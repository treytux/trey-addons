###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestStockPickingBatchPackageNumber(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Test partner 1',
            'is_company': True,
        })
        self.partner_02 = self.partner_01.copy()
        self.partner_02.name = 'Test partner 2'
        self.free_delivery = self.env.ref('delivery.free_delivery_carrier')
        self.product_01 = self.env['product.product'].create({
            'name': 'Product test 01',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        self.product_02 = self.env['product.product'].create({
            'name': 'Product test 01',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        self.sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'carrier_id': self.free_delivery.id,
            'order_line': [(0, 0, {
                'product_id': self.product_01.id,
                'product_uom_qty': 2,
            })]
        })
        self.sale_01.action_confirm()
        self.sale_02 = self.env['sale.order'].create({
            'partner_id': self.partner_02.id,
            'carrier_id': self.free_delivery.id,
            'order_line': [(0, 0, {
                'product_id': self.product_02.id,
                'product_uom_qty': 3,
            })]
        })
        self.sale_02.action_confirm()
        self.picking_01 = self.sale_01.picking_ids[0]
        self.picking_02 = self.sale_02.picking_ids[0]
        self.picking_01.name = 'PICKING_01'
        self.picking_02.name = 'PICKING_02'
        self.batch = self.env['stock.picking.batch'].create({
            'name': 'Batch 1',
            'picking_ids': [
                [6, False, [self.picking_01.id, self.picking_02.id]]
            ],
            'carrier_id': False,
        })

    def test_create_batch_and_validate_all_pickings(self):
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.env.ref('stock.stock_location_stock'), 10.0)
        self.batch.confirm_picking()
        self.assertEqual(self.picking_01.state, 'assigned')
        self.assertEqual(self.picking_02.state, 'assigned')
        res = self.batch.action_transfer()
        self.assertEqual(res.get('res_model'), 'stock.immediate.transfer')
        wizard = self.env[(res.get('res_model'))].browse(res.get('res_id'))
        self.assertFalse(wizard.hide_line_ids)
        self.assertEqual(len(wizard.line_ids), 2)
        line_01 = wizard.line_ids.filtered(
            lambda ln: ln.picking_id.name == 'PICKING_01')
        line_02 = wizard.line_ids.filtered(
            lambda ln: ln.picking_id.name == 'PICKING_02')
        line_01.number_of_packages = 2
        line_02.number_of_packages = 3
        self.assertEqual(line_01.number_of_packages, 2)
        self.assertEqual(line_02.number_of_packages, 3)
        wizard.process()
        self.assertEqual(self.picking_01.state, 'done')
        self.assertEqual(self.picking_02.state, 'done')
        self.assertEqual(self.picking_01.number_of_packages, 2)
        self.assertEqual(self.picking_02.number_of_packages, 3)

    def test_create_batch_and_create_partial_shipping_01(self):
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.env.ref('stock.stock_location_stock'), 10.0)
        self.batch.confirm_picking()
        self.assertEqual(self.picking_01.state, 'assigned')
        self.assertEqual(self.picking_02.state, 'assigned')
        self.picking_01.move_lines.quantity_done = 2
        self.picking_02.move_lines.quantity_done = 1
        res = self.batch.action_transfer()
        self.assertEqual(res.get('res_model'), 'stock.backorder.confirmation')
        wizard = self.env[(res.get('res_model'))].browse(res.get('res_id'))
        self.assertFalse(wizard.hide_line_ids)
        self.assertEqual(len(wizard.line_ids), 2)
        line_01 = wizard.line_ids.filtered(
            lambda ln: ln.picking_id.name == 'PICKING_01')
        line_02 = wizard.line_ids.filtered(
            lambda ln: ln.picking_id.name == 'PICKING_02')
        line_01.number_of_packages = 2
        line_02.number_of_packages = 3
        self.assertEqual(line_01.number_of_packages, 2)
        self.assertEqual(line_02.number_of_packages, 3)
        wizard.process()
        self.assertEqual(self.picking_01.state, 'done')
        self.assertEqual(self.picking_02.state, 'done')
        self.assertEqual(self.picking_01.number_of_packages, 2)
        self.assertEqual(self.picking_02.number_of_packages, 3)
        self.assertEqual(len(self.sale_02.picking_ids), 2)
        picking = self.sale_02.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(picking.move_lines.product_uom_qty, 2)
        self.assertEqual(picking.number_of_packages, 1)

    def test_create_batch_and_create_partial_shipping_02(self):
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.env.ref('stock.stock_location_stock'), 10.0)
        self.batch.confirm_picking()
        self.assertEqual(self.picking_01.state, 'assigned')
        self.assertEqual(self.picking_02.state, 'assigned')
        self.picking_01.move_lines.quantity_done = 2
        self.picking_02.move_lines.quantity_done = 2
        res = self.batch.action_transfer()
        self.assertEqual(res.get('res_model'), 'stock.backorder.confirmation')
        wizard = self.env[(res.get('res_model'))].browse(res.get('res_id'))
        self.assertFalse(wizard.hide_line_ids)
        self.assertEqual(len(wizard.line_ids), 2)
        line_01 = wizard.line_ids.filtered(
            lambda ln: ln.picking_id.name == 'PICKING_01')
        line_02 = wizard.line_ids.filtered(
            lambda ln: ln.picking_id.name == 'PICKING_02')
        line_01.number_of_packages = 2
        line_02.number_of_packages = 3
        self.assertEqual(line_01.number_of_packages, 2)
        self.assertEqual(line_02.number_of_packages, 3)
        wizard.process_cancel_backorder()
        self.assertEqual(self.picking_01.state, 'done')
        self.assertEqual(self.picking_02.state, 'done')
        self.assertEqual(self.picking_01.number_of_packages, 2)
        self.assertEqual(self.picking_02.number_of_packages, 3)
        self.assertEqual(len(self.sale_02.picking_ids), 2)
        picking_cancel = self.sale_02.picking_ids.filtered(
            lambda p: p.state == 'cancel')
        picking_done = self.sale_02.picking_ids.filtered(
            lambda p: p.state == 'done')
        self.assertEqual(len(picking_cancel), 1)
        self.assertEqual(len(picking_done), 1)

    def test_create_batch_and_validate_two_times(self):
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.env.ref('stock.stock_location_stock'), 10.0)
        self.batch.confirm_picking()
        self.assertEqual(self.batch.state, 'assigned')
        self.assertEqual(self.picking_01.state, 'assigned')
        self.assertEqual(self.picking_02.state, 'assigned')
        self.picking_01.move_lines.quantity_done = 2
        res = self.batch.action_transfer()
        self.assertEqual(res.get('res_model'), 'stock.backorder.confirmation')
        wizard = self.env[(res.get('res_model'))].browse(res.get('res_id'))
        self.assertFalse(wizard.hide_line_ids)
        self.assertEqual(len(wizard.line_ids), 1)
        wizard.line_ids[0].number_of_packages = 2
        self.assertEqual(wizard.line_ids[0].number_of_packages, 2)
        wizard.process()
        self.assertEqual(self.picking_01.state, 'done')
        self.assertEqual(self.picking_02.state, 'assigned')
        self.assertEqual(self.batch.state, 'assigned')
        res = self.batch.action_transfer()
        self.assertEqual(res.get('res_model'), 'stock.immediate.transfer')
        wizard = self.env[(res.get('res_model'))].browse(res.get('res_id'))
        self.assertFalse(wizard.hide_line_ids)
        self.assertEqual(len(wizard.line_ids), 1)
        wizard.line_ids[0].number_of_packages = 4
        self.assertEqual(wizard.line_ids[0].number_of_packages, 4)
        wizard.process()
        self.assertEqual(self.picking_01.state, 'done')
        self.assertEqual(self.picking_02.state, 'done')
        self.assertEqual(self.batch.state, 'done')
