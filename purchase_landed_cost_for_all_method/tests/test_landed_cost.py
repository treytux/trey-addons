###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import time

from odoo import fields
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestLandedCost(TransactionCase):

    def setUp(self):
        super().setUp()
        self.supplier = self._create_record(
            model_name='res.partner',
            vals={
                'name': 'Supplier test',
                'supplier': True,
                'delivery_slip_type': 'valued',
            },
        )
        user_type = self.env.ref('account.data_account_type_expenses')
        self.account = self._create_record(
            model_name='account.account',
            vals={
                'name': 'Account',
                'code': 'CODE',
                'user_type_id': user_type.id,
            },
        )
        self.product_no_tracking = self._create_record(
            model_name='product.product',
            vals={
                'name': 'Product',
                'type': 'product',
                'default_code': 'PRODUCT',
                'standard_price': 1,
                'property_account_expense_id': self.account.id,
            },
        )
        self.product_tracking_lot = self._create_record(
            model_name='product.product',
            vals={
                'name': 'Product with lot',
                'type': 'product',
                'default_code': 'PRODUCT-LOT',
                'standard_price': 1,
                'property_account_expense_id': self.account.id,
                'tracking': 'lot',
            },
        )
        self.cost = self._create_record(
            model_name='product.product',
            vals={
                'name': 'Landed cost',
                'type': 'product',
                'default_code': 'COST',
                'standard_price': 1,
                'property_account_expense_id': self.account.id,
            },
        )
        self.type_amount = self._create_record(
            model_name='purchase.expense.type',
            vals={
                'name': 'Amount line',
                'calculation_method': 'amount',
            },
        )
        self.stock_location = self.env.ref('stock.stock_location_stock')

    def _create_record(self, model_name, vals):
        record = self._create_vals(model_name, vals)
        return record.create(record._convert_to_write(record._cache))

    def _create_vals(self, model_name, vals):
        model = self.env[model_name]
        data = model.default_get(list(model.fields_get()))
        data.update(vals)
        return model.new(data)

    def _create_picking(
            self, in_or_out, product, qty, price_unit=None, lot=None):
        if in_or_out == 'in':
            assert price_unit, 'You must assign price_unit for in moves!'
            location_src = self.env.ref('stock.stock_location_suppliers')
            location_dst = self.stock_location
            sign_price = 1
        elif in_or_out == 'out':
            assert not price_unit, (
                'You must not assign price_unit for out moves!')
            location_src = self.stock_location
            location_dst = self.env.ref('stock.stock_location_customers')
            sign_price = -1
        picking_type = self.env.ref(f'stock.picking_type_{in_or_out}')
        data_move_lines = {
            'product_id': product.id,
            'name': product.name,
            'product_uom': product.uom_id.id,
            'product_uom_qty': qty,
            'procure_method': 'make_to_stock',
            # @TODO En el mrp_cost_price puede estar mal, esto no
            # se reseteaba a draft, y si no lo está, el método
            # product_price_update_before_done no hace nada de
            # actualizar el precio de coste
            # addons/stock_account/models/stock.py:435
            'state': 'draft',
        }
        if in_or_out == 'in':
            data_move_lines.update({
                'price_unit': sign_price * price_unit,
                'value': sign_price * qty * price_unit,
            })
        if lot:
            data_move_lines.update({
                'lot_id': lot.id,
            })
        new_picking = self._create_vals(
            model_name='stock.picking',
            vals={
                'location_id': location_src.id,
                'location_dest_id': location_dst.id,
                'picking_type_id': picking_type.id,
                'move_lines': [
                    (0, 0, data_move_lines),
                ],
            },
        )
        new_picking.onchange_picking_type()
        new_picking.move_lines.onchange_product_id()
        picking = new_picking.create(
            new_picking._convert_to_write(new_picking._cache))
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            if lot:
                move_line.lot_id = lot.id
            move_line.qty_done = move_line.product_uom_qty
        picking.action_done()
        time.sleep(1)
        return picking

    def _create_pickings(
            self, number_of_pickings, in_or_out, product, qty, price_unit,
            lot=None):
        pickings = []
        for _count in range(number_of_pickings):
            picking = self._create_picking(
                in_or_out, product, qty, price_unit, lot)
            pickings.append(picking)
        return pickings

    def _create_purchase_order(self, product, qty, price_unit):
        purchase = self._create_record(
            model_name='purchase.order',
            vals={
                'partner_id': self.supplier.id,
                'order_line': [
                    (0, 0, {
                        'product_id': product.id,
                        'product_qty': qty,
                        'name': product.name,
                        'product_uom': product.uom_id.id,
                        'price_unit': price_unit,
                        'date_planned': fields.Datetime.now(),
                    }),
                ],
            },
        )
        purchase.button_confirm()
        return purchase

    def _create_invoice(self, product, qty, price_unit):
        invoice = self._create_record(
            model_name='account.invoice',
            vals={
                'partner_id': self.supplier.id,
                'type': 'in_invoice',
                'invoice_line_ids': [
                    (0, 0, {
                        'name': 'Test service',
                        'account_id': product.property_account_expense_id.id,
                        'product_uom_qty': qty,
                        'product_uom_id': product.uom_id.id,
                        'price_unit': price_unit,
                    }),
                ],
            },
        )
        invoice.action_invoice_open()
        return invoice

    def _create_inventory(self, location, product, qty, lot=None):
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': location.id,
            'exhausted': True,
        })
        inventory.action_start()
        line_data = {
            'inventory_id': inventory.id,
            'product_id': product.id,
            'product_qty': qty,
            'location_id': location.id,
        }
        if lot:
            line_data.update({
                'prod_lot_id': lot.id,
            })
        inventory.line_ids.create(line_data)
        inventory._action_done()
        time.sleep(1)
        return inventory

    # @TODO A falta de comprobaciones de la tabla "stock.move.line.relation"
    def TODOtest_landed_cost_standard_product_no_tracking(self):
        self.product_no_tracking.standard_price = 10
        self.product_no_tracking.categ_id.property_cost_method = 'standard'
        self.assertEqual(self.product_no_tracking.standard_price, 10)
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=10000)
        self.assertEqual(self.product_no_tracking.standard_price, 10)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 50)
        self.assertEqual(picking_in_01.move_lines.price_unit, 10)
        self.assertEqual(picking_in_01.move_lines.value, 50)
        purchase = self._create_purchase_order(
            self.product_no_tracking, qty=2, price_unit=100)
        self.assertEqual(purchase.order_line[0].price_unit, 100)
        self.assertEqual(purchase.amount_untaxed, 200)
        self.assertEqual(len(purchase.picking_ids), 1)
        picking_in_02 = purchase.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 10)
        picking_in_02.action_done()
        self.assertEqual(self.product_no_tracking.standard_price, 10)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 70)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_02.move_lines.value, 20)
        self.assertEqual(picking_in_02.move_lines.price_unit, 10)
        self.assertEqual(picking_in_02.state, 'done')
        # Distribucion 1 IN002 1000€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=500)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_02.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        cost_line = distribution.cost_lines
        self.assertEqual(cost_line.product_qty, 2)
        self.assertEqual(cost_line.product_price_unit, 10)
        self.assertEqual(cost_line.standard_price_old, 10)
        self.assertEqual(cost_line.standard_price_new, 260)
        self.assertEqual(len(cost_line.expense_lines), 1)
        expense_line = cost_line.expense_lines
        self.assertEqual(expense_line.expense_amount, 500)
        self.assertEqual(expense_line.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 2)
        self.assertEqual(distribution.total_purchase, 20)
        self.assertEqual(distribution.total_expense, 500)
        self.assertEqual(self.product_no_tracking.standard_price, 10)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 70)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_no_tracking.standard_price, 10)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 570)
        distribution.action_cancel()
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 70)
        self.assertEqual(self.product_no_tracking.standard_price, 10)
        self.assertEqual(picking_in_01.move_lines.price_unit, 10)
        self.assertEqual(picking_in_01.move_lines.value, 50)
        # self.assertEqual(picking_in_02.move_lines.price_unit, 260)
        # self.assertEqual(picking_in_02.move_lines.value, 1300)
        # # OUT001 qty=1; price_unit=100
        # picking_out_01 = self._create_picking(
        #     'out', self.product_no_tracking, qty=1, price_unit=100)
        # self.assertEqual(self.product_no_tracking.standard_price, 10)
        # self.assertEqual(picking_out_01.move_lines.price_unit, -10)
        # self.assertEqual(picking_out_01.move_lines.value, -10)

    # @TODO A falta de comprobaciones de la tabla "stock.move.line.relation"
    def TODOtest_landed_cost_average_product_no_tracking(self):
        self.product_no_tracking.categ_id.property_cost_method = 'average'
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=10)
        self.assertEqual(self.product_no_tracking.standard_price, 10)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 50)
        purchase = self._create_purchase_order(
            self.product_no_tracking, qty=2, price_unit=100)
        self.assertEqual(purchase.order_line[0].price_unit, 100)
        self.assertEqual(purchase.amount_untaxed, 200)
        self.assertEqual(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 10)
        picking.action_done()
        self.assertEqual(self.product_no_tracking.standard_price, 35.71)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 250)
        self.assertEqual(picking.move_lines.quantity_done, 2)
        self.assertEqual(picking.move_lines.value, 200)
        self.assertEqual(picking.move_lines.price_unit, 100)
        self.assertEqual(picking.state, 'done')
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=500)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        cost_line = distribution.cost_lines
        self.assertEqual(cost_line.product_qty, 2)
        self.assertEqual(cost_line.product_price_unit, 100)
        self.assertEqual(cost_line.standard_price_old, 100)
        self.assertEqual(cost_line.standard_price_new, 350)
        self.assertEqual(len(cost_line.expense_lines), 1)
        expense_line = cost_line.expense_lines
        self.assertEqual(expense_line.expense_amount, 500)
        self.assertEqual(expense_line.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 2)
        self.assertEqual(distribution.total_purchase, 200)
        self.assertEqual(distribution.total_expense, 500)
        self.assertEqual(self.product_no_tracking.standard_price, 35.71)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_no_tracking.standard_price, 107.14)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 750)
        distribution.action_cancel()
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 250)
        self.assertEqual(self.product_no_tracking.standard_price, 35.71)

    def test_landed_cost_fifo_product_tracking_lot_01(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        # IN001 qty=2; price_unit=150€; lot=001
        purchase_01 = self._create_purchase_order(
            self.product_tracking_lot, qty=2, price_unit=150)
        self.assertEqual(purchase_01.order_line[0].price_unit, 150)
        self.assertEqual(purchase_01.amount_untaxed, 300)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01.move_line_ids[0].lot_id = lot_001.id
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 300)
        # IN002 qty=4; price_unit=100€; lot=002
        purchase_02 = self._create_purchase_order(
            self.product_tracking_lot, qty=4, price_unit=100)
        self.assertEqual(purchase_02.order_line[0].price_unit, 100)
        self.assertEqual(purchase_02.amount_untaxed, 400)
        self.assertEqual(len(purchase_02.picking_ids), 1)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02.move_line_ids[0].lot_id = lot_002.id
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_02.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 700)
        # OUT001 qty=3; price_unit=150€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(len(picking_out_01.move_line_ids), 2)
        self.assertEqual(picking_out_01.move_line_ids[0].qty_done, 2)
        self.assertEqual(picking_out_01.move_line_ids[0].lot_id, lot_001)
        self.assertEqual(picking_out_01.move_line_ids[1].qty_done, 1)
        self.assertEqual(picking_out_01.move_line_ids[1].lot_id, lot_002)
        self.assertEqual(
            round(picking_out_01.move_lines.price_unit, 2), -133.33)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -400)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 300)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_in_02 = picking_in_02.move_line_ids
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01), 2)
        move_line_out_01_01 = move_lines_out_01.filtered(
            lambda ml: ml.qty_done == 2 and ml.lot_id == lot_001)
        self.assertEquals(len(move_line_out_01_01), 1)
        self.assertEquals(len(move_line_out_01_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_out_01_01.move_line_relation_ids.quantity, 2)
        self.assertEquals(
            move_line_out_01_01.move_line_relation_ids.price_unit, 150)
        move_line_out_01_02 = move_lines_out_01.filtered(
            lambda ml: ml.qty_done == 1 and ml.lot_id == lot_002)
        self.assertEquals(len(move_line_out_01_02), 1)
        self.assertEquals(len(move_line_out_01_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01_02.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(
            move_line_out_01_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01_02.move_line_relation_ids.price_unit, 100)

    def test_landed_cost_fifo_product_tracking_lot_02(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        # IN001 qty=2; price_unit=150€; lot=001
        purchase_01 = self._create_purchase_order(
            self.product_tracking_lot, qty=2, price_unit=150)
        self.assertEqual(purchase_01.order_line[0].price_unit, 150)
        self.assertEqual(purchase_01.amount_untaxed, 300)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01.move_line_ids[0].lot_id = lot_001.id
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 300)
        # IN002 qty=4; price_unit=100€; lot=002
        purchase_02 = self._create_purchase_order(
            self.product_tracking_lot, qty=4, price_unit=100)
        self.assertEqual(purchase_02.order_line[0].price_unit, 100)
        self.assertEqual(purchase_02.amount_untaxed, 400)
        self.assertEqual(len(purchase_02.picking_ids), 1)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02.move_line_ids[0].lot_id = lot_002.id
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_02.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 700)
        # OUT001 qty=3; price_unit=133.33€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(len(picking_out_01.move_line_ids), 2)
        self.assertEqual(picking_out_01.move_line_ids[0].qty_done, 2)
        self.assertEqual(picking_out_01.move_line_ids[0].lot_id, lot_001)
        self.assertEqual(picking_out_01.move_line_ids[1].qty_done, 1)
        self.assertEqual(picking_out_01.move_line_ids[1].lot_id, lot_002)
        self.assertEqual(
            round(picking_out_01.move_lines.price_unit, 2), -133.33)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -400)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 300)
        # OUT002 qty=1; price_unit=100€
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=1)
        self.assertEqual(len(picking_out_02.move_line_ids), 1)
        self.assertEqual(picking_out_02.move_line_ids[0].qty_done, 1)
        self.assertEqual(picking_out_02.move_line_ids[0].lot_id, lot_002)
        self.assertEqual(picking_out_02.move_lines.price_unit, -100)
        self.assertEqual(picking_out_02.move_lines.product_uom_qty, 1)
        self.assertEqual(picking_out_02.move_lines.value, -100)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 200)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_in_02 = picking_in_02.move_line_ids
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01), 2)
        move_line_out_01_01 = move_lines_out_01.filtered(
            lambda ml: ml.qty_done == 2 and ml.lot_id == lot_001)
        self.assertEquals(len(move_line_out_01_01), 1)
        self.assertEquals(len(move_line_out_01_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_out_01_01.move_line_relation_ids.quantity, 2)
        self.assertEquals(
            move_line_out_01_01.move_line_relation_ids.price_unit, 150)
        move_line_out_01_02 = move_lines_out_01.filtered(
            lambda ml: ml.qty_done == 1 and ml.lot_id == lot_002)
        self.assertEquals(len(move_line_out_01_02), 1)
        self.assertEquals(len(move_line_out_01_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01_02.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(
            move_line_out_01_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01_02.move_line_relation_ids.price_unit, 100)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 100)

    def test_landed_cost_fifo_product_tracking_lot_03(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        # IN001 qty=2; price_unit=150€; lot=001
        purchase_01 = self._create_purchase_order(
            self.product_tracking_lot, qty=2, price_unit=150)
        self.assertEqual(purchase_01.order_line[0].price_unit, 150)
        self.assertEqual(purchase_01.amount_untaxed, 300)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01.move_line_ids[0].lot_id = lot_001.id
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 300)
        # IN002 qty=4; price_unit=100€; lot=002
        purchase_02 = self._create_purchase_order(
            self.product_tracking_lot, qty=4, price_unit=100)
        self.assertEqual(purchase_02.order_line[0].price_unit, 100)
        self.assertEqual(purchase_02.amount_untaxed, 400)
        self.assertEqual(len(purchase_02.picking_ids), 1)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02.move_line_ids[0].lot_id = lot_002.id
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_02.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 700)
        # IN003 qty=10; price_unit=200€; lot=001
        purchase_03 = self._create_purchase_order(
            self.product_tracking_lot, qty=10, price_unit=200)
        self.assertEqual(purchase_03.order_line[0].price_unit, 200)
        self.assertEqual(purchase_03.amount_untaxed, 2000)
        self.assertEqual(len(purchase_03.picking_ids), 1)
        picking_in_03 = purchase_03.picking_ids
        picking_in_03.action_confirm()
        picking_in_03.action_assign()
        picking_in_03.move_line_ids[0].lot_id = lot_001.id
        for move in picking_in_03.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_03.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_03.move_lines.quantity_done, 10)
        self.assertEqual(picking_in_03.move_lines.price_unit, 200)
        self.assertEqual(picking_in_03.move_lines.value, 2000)
        self.assertEqual(picking_in_03.move_lines.remaining_qty, 10)
        self.assertEqual(picking_in_03.move_lines.remaining_value, 2000)
        self.assertEqual(picking_in_03.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            2700)
        # OUT001 qty=3; price_unit=133.33€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(len(picking_out_01.move_line_ids), 1)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 3)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_line_ids.lot_id, lot_001)
        self.assertEqual(
            round(picking_out_01.move_lines.price_unit, 2), -133.33)
        self.assertEqual(picking_out_01.move_lines.value, -400)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_03.move_lines.price_unit, 200)
        self.assertEqual(picking_in_03.move_lines.value, 2000)
        self.assertEqual(picking_in_03.move_lines.remaining_qty, 10)
        self.assertEqual(picking_in_03.move_lines.remaining_value, 2000)
        # OUT002 qty=1; price_unit=100€
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=1)
        self.assertEqual(len(picking_out_02.move_line_ids), 1)
        self.assertEqual(picking_out_02.move_line_ids[0].qty_done, 1)
        self.assertEqual(picking_out_02.move_line_ids[0].lot_id, lot_001)
        self.assertEqual(picking_out_02.move_lines.price_unit, -100)
        self.assertEqual(picking_out_02.move_lines.value, -100)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_in_03 = picking_in_03.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01), 1)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_line_rel_1 = move_line_out_01.move_line_relation_ids[0]
        move_line_rel_2 = move_line_out_01.move_line_relation_ids[1]
        self.assertEqual(move_line_rel_1.move_line_id, move_line_in_01)
        self.assertEqual(move_line_rel_1.quantity, 2)
        self.assertEqual(move_line_rel_1.price_unit, 150)
        self.assertEqual(move_line_rel_2.move_line_id, move_line_in_03)
        self.assertEqual(move_line_rel_2.quantity, 1)
        self.assertEqual(move_line_rel_2.price_unit, 200)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_03)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 200)

    def test_landed_cost_fifo_product_tracking_lot_04(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        # IN001 qty=2; price_unit=150€; lot=001
        purchase_01 = self._create_purchase_order(
            self.product_tracking_lot, qty=2, price_unit=150)
        self.assertEqual(purchase_01.order_line[0].price_unit, 150)
        self.assertEqual(purchase_01.amount_untaxed, 300)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01.move_line_ids[0].lot_id = lot_001.id
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 300)
        # IN002 qty=4; price_unit=100€; lot=002
        purchase_02 = self._create_purchase_order(
            self.product_tracking_lot, qty=4, price_unit=100)
        self.assertEqual(purchase_02.order_line[0].price_unit, 100)
        self.assertEqual(purchase_02.amount_untaxed, 400)
        self.assertEqual(len(purchase_02.picking_ids), 1)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02.move_line_ids[0].lot_id = lot_002.id
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_02.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 700)
        # IN003 qty=10; price_unit=200€; lot=001
        purchase_03 = self._create_purchase_order(
            self.product_tracking_lot, qty=10, price_unit=200)
        self.assertEqual(purchase_03.order_line[0].price_unit, 200)
        self.assertEqual(purchase_03.amount_untaxed, 2000)
        self.assertEqual(len(purchase_03.picking_ids), 1)
        picking_in_03 = purchase_03.picking_ids
        picking_in_03.action_confirm()
        picking_in_03.action_assign()
        picking_in_03.move_line_ids[0].lot_id = lot_001.id
        for move in picking_in_03.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_03.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_03.move_lines.quantity_done, 10)
        self.assertEqual(picking_in_03.move_lines.price_unit, 200)
        self.assertEqual(picking_in_03.move_lines.value, 2000)
        self.assertEqual(picking_in_03.move_lines.remaining_qty, 10)
        self.assertEqual(picking_in_03.move_lines.remaining_value, 2000)
        self.assertEqual(picking_in_03.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            2700)
        # OUT001 qty=3; price_unit=133.33€; force lot=001
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3, lot=lot_001)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(len(picking_out_01.move_line_ids), 1)
        self.assertEqual(picking_out_01.move_line_ids[0].qty_done, 3)
        self.assertEqual(picking_out_01.move_line_ids[0].lot_id, lot_001)
        self.assertEqual(
            round(picking_out_01.move_lines.price_unit, 2), -133.33)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -400)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_03.move_lines.price_unit, 200)
        self.assertEqual(picking_in_03.move_lines.value, 2000)
        self.assertEqual(picking_in_03.move_lines.remaining_qty, 10)
        self.assertEqual(picking_in_03.move_lines.remaining_value, 2000)
        # OUT002 qty=1; price_unit=100€, force lot=001
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, lot=lot_001)
        self.assertEqual(len(picking_out_02.move_line_ids), 1)
        self.assertEqual(picking_out_02.move_line_ids[0].qty_done, 1)
        self.assertEqual(picking_out_02.move_line_ids[0].lot_id, lot_001)
        self.assertEqual(picking_out_02.move_lines.price_unit, -100)
        self.assertEqual(picking_out_02.move_lines.product_uom_qty, 1)
        self.assertEqual(picking_out_02.move_lines.value, -100)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        # OUT003 qty=9; price_unit=177.78€
        picking_out_03 = self._create_picking(
            'out', self.product_tracking_lot, qty=9)
        self.assertEqual(len(picking_out_03.move_line_ids), 2)
        self.assertEqual(picking_out_03.move_line_ids[0].qty_done, 8)
        self.assertEqual(picking_out_03.move_line_ids[0].lot_id, lot_001)
        self.assertEqual(picking_out_03.move_line_ids[1].qty_done, 1)
        self.assertEqual(picking_out_03.move_line_ids[1].lot_id, lot_002)
        self.assertEqual(picking_out_03.move_lines.product_uom_qty, 9)
        self.assertEqual(
            round(picking_out_03.move_lines.price_unit, 2), -177.78)
        self.assertEqual(picking_out_03.move_lines.value, -1600)
        self.assertEqual(self.product_tracking_lot.standard_price, 200)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_in_02 = picking_in_02.move_line_ids
        move_line_in_03 = picking_in_03.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01), 1)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_line_rel_1 = move_line_out_01.move_line_relation_ids[0]
        move_line_rel_2 = move_line_out_01.move_line_relation_ids[1]
        self.assertEqual(move_line_rel_1.move_line_id, move_line_in_01)
        self.assertEqual(move_line_rel_1.quantity, 2)
        self.assertEqual(move_line_rel_1.price_unit, 150)
        self.assertEqual(move_line_rel_2.move_line_id, move_line_in_03)
        self.assertEqual(move_line_rel_2.quantity, 1)
        self.assertEqual(move_line_rel_2.price_unit, 200)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_03)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 200)
        move_lines_out_03 = picking_out_03.move_line_ids
        self.assertEquals(len(move_lines_out_03), 2)
        move_line_out_03_01 = move_lines_out_03.filtered(
            lambda ml: ml.qty_done == 8 and ml.lot_id == lot_001)
        self.assertEquals(len(move_line_out_03_01), 1)
        self.assertEquals(len(move_line_out_03_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_03_01.move_line_relation_ids.move_line_id,
            move_line_in_03)
        self.assertEquals(
            move_line_out_03_01.move_line_relation_ids.quantity, 8)
        self.assertEquals(
            move_line_out_03_01.move_line_relation_ids.price_unit, 200)
        move_line_out_03_02 = move_lines_out_03.filtered(
            lambda ml: ml.qty_done == 1 and ml.lot_id == lot_002)
        self.assertEquals(len(move_line_out_03_02), 1)
        self.assertEquals(len(move_line_out_03_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_03_02.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(
            move_line_out_03_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_03_02.move_line_relation_ids.price_unit, 100)

    def test_landed_cost_fifo_product_tracking_lot_05(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        # IN001 qty=4; price_unit=100€; lot=001
        purchase_01 = self._create_purchase_order(
            self.product_tracking_lot, qty=4, price_unit=100)
        self.assertEqual(purchase_01.order_line[0].price_unit, 100)
        self.assertEqual(purchase_01.amount_untaxed, 400)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01.move_line_ids[0].lot_id = lot_001.id
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 400)
        # OUT001 qty=1; price_unit=100€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(picking_out_01.move_lines.price_unit, -100)
        self.assertEqual(picking_out_01.move_lines.value, -100)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        # Distribucion 1 IN001 1000€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=1000)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        cost_line = distribution.cost_lines
        self.assertEqual(cost_line.product_qty, 4)
        self.assertEqual(cost_line.product_price_unit, 100)
        self.assertEqual(cost_line.standard_price_old, 100)
        self.assertEqual(cost_line.standard_price_new, 350)
        self.assertEqual(len(cost_line.expense_lines), 1)
        expense_line = cost_line.expense_lines
        self.assertEqual(expense_line.expense_amount, 1000)
        self.assertEqual(expense_line.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 4)
        self.assertEqual(distribution.total_purchase, 400)
        self.assertEqual(distribution.total_expense, 1000)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 350)
        self.assertEqual(picking_in_01.move_lines.price_unit, 350)
        self.assertEqual(picking_in_01.move_lines.value, 1400)
        self.assertEqual(picking_out_01.move_lines.price_unit, -350)
        self.assertEqual(picking_out_01.move_lines.value, -350)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 350)
        # OUT002 qty=1; price_unit=350€
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=1)
        self.assertEqual(self.product_tracking_lot.standard_price, 350)
        self.assertEqual(picking_out_02.move_lines.price_unit, -350)
        self.assertEqual(picking_out_02.move_lines.value, -350)
        self.assertEqual(picking_in_01.move_lines.price_unit, 350)
        self.assertEqual(picking_in_01.move_lines.value, 1400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 700)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 350)
        # Distribucion 2 IN001 1000€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=1000)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        cost_line = distribution.cost_lines
        self.assertEqual(cost_line.product_qty, 4)
        self.assertEqual(cost_line.product_price_unit, 350)
        self.assertEqual(cost_line.standard_price_old, 350)
        self.assertEqual(cost_line.standard_price_new, 600)
        self.assertEqual(len(cost_line.expense_lines), 1)
        expense_line = cost_line.expense_lines
        self.assertEqual(expense_line.expense_amount, 1000)
        self.assertEqual(expense_line.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 4)
        self.assertEqual(distribution.total_purchase, 1400)
        self.assertEqual(distribution.total_expense, 1000)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 600)
        self.assertEqual(picking_in_01.move_lines.price_unit, 600)
        self.assertEqual(picking_in_01.move_lines.value, 2400)
        self.assertEqual(picking_out_01.move_lines.price_unit, -600)
        self.assertEqual(picking_out_01.move_lines.value, -600)
        self.assertEqual(picking_out_02.move_lines.price_unit, -600)
        self.assertEqual(picking_out_02.move_lines.value, -600)
        # IN002 qty=2; price_unit=150; lot=002
        purchase_02 = self._create_purchase_order(
            self.product_tracking_lot, qty=2, price_unit=150)
        self.assertEqual(purchase_02.order_line[0].price_unit, 150)
        self.assertEqual(purchase_02.amount_untaxed, 300)
        self.assertEqual(len(purchase_02.picking_ids), 1)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02.move_line_ids[0].lot_id = lot_002.id
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 600)
        picking_in_02.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 600)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_02.move_lines.price_unit, 150)
        self.assertEqual(picking_in_02.move_lines.value, 300)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            1500)
        # OUT003 qty=2; price_unit=600€
        picking_out_03 = self._create_picking(
            'out', self.product_tracking_lot, qty=2)
        # Porque ha cambiado el quant
        self.assertEqual(self.product_tracking_lot.standard_price, 150)
        self.assertEqual(picking_out_03.move_lines.price_unit, -600)
        self.assertEqual(picking_out_03.move_lines.value, -1200)
        self.assertEqual(picking_in_01.move_lines.price_unit, 600)
        self.assertEqual(picking_in_01.move_lines.value, 2400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        move_line_out_03 = picking_out_03.move_line_ids
        self.assertEquals(len(move_line_out_03.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_03.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_03.move_line_relation_ids.quantity, 2)
        self.assertEquals(
            move_line_out_03.move_line_relation_ids.price_unit, 600)
        # Distribucion 3 IN001 1000€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=1000)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        cost_line = distribution.cost_lines
        self.assertEqual(cost_line.product_qty, 4)
        self.assertEqual(cost_line.product_price_unit, 600)
        self.assertEqual(cost_line.standard_price_old, 600)
        self.assertEqual(cost_line.standard_price_new, 850)
        self.assertEqual(len(cost_line.expense_lines), 1)
        expense_line = cost_line.expense_lines
        self.assertEqual(expense_line.expense_amount, 1000)
        self.assertEqual(expense_line.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 4)
        self.assertEqual(distribution.total_purchase, 2400)
        self.assertEqual(distribution.total_expense, 1000)
        self.assertEqual(self.product_tracking_lot.standard_price, 150)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(self.product_tracking_lot.standard_price, 150)
        self.assertEqual(picking_in_01.move_lines.price_unit, 850)
        self.assertEqual(picking_in_01.move_lines.value, 3400)
        self.assertEqual(picking_out_01.move_lines.price_unit, -850)
        self.assertEqual(picking_out_01.move_lines.value, -850)
        self.assertEqual(picking_out_02.move_lines.price_unit, -850)
        self.assertEqual(picking_out_02.move_lines.value, -850)
        self.assertEqual(picking_out_03.move_lines.price_unit, - 850)
        self.assertEqual(picking_out_03.move_lines.value, -1700)

    def test_landed_cost_fifo_product_tracking_lot_06_cancel_distrib(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        # IN001 qty=4; price_unit=100€; lot=001
        purchase_01 = self._create_purchase_order(
            self.product_tracking_lot, qty=4, price_unit=100)
        self.assertEqual(purchase_01.order_line[0].price_unit, 100)
        self.assertEqual(purchase_01.amount_untaxed, 400)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01.move_line_ids[0].lot_id = lot_001.id
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 400)
        # OUT001 qty=1; price_unit=100€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(picking_out_01.move_lines.price_unit, -100)
        self.assertEqual(picking_out_01.move_lines.value, -100)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        # Distribucion 1 IN001 1000€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=1000)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        cost_line = distribution.cost_lines
        self.assertEqual(cost_line.product_qty, 4)
        self.assertEqual(cost_line.product_price_unit, 100)
        self.assertEqual(cost_line.standard_price_old, 100)
        self.assertEqual(cost_line.standard_price_new, 350)
        self.assertEqual(len(cost_line.expense_lines), 1)
        expense_line = cost_line.expense_lines
        self.assertEqual(expense_line.expense_amount, 1000)
        self.assertEqual(expense_line.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 4)
        self.assertEqual(distribution.total_purchase, 400)
        self.assertEqual(distribution.total_expense, 1000)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 350)
        self.assertEqual(picking_in_01.move_lines.price_unit, 350)
        self.assertEqual(picking_in_01.move_lines.value, 1400)
        self.assertEqual(picking_out_01.move_lines.price_unit, -350)
        self.assertEqual(picking_out_01.move_lines.value, -350)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 350)
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            1050)
        distribution.action_cancel()
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 300)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 350)
        self.assertEqual(picking_in_01.move_lines.price_unit, 350)
        self.assertEqual(picking_in_01.move_lines.value, 1400)
        self.assertEqual(picking_out_01.move_lines.price_unit, -350)
        self.assertEqual(picking_out_01.move_lines.value, -350)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 350)
        # OUT002 qty=1; price_unit=350€
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=1)
        self.assertEqual(self.product_tracking_lot.standard_price, 350)
        self.assertEqual(picking_out_02.move_lines.price_unit, -350)
        self.assertEqual(picking_out_02.move_lines.value, -350)
        self.assertEqual(picking_in_01.move_lines.price_unit, 350)
        self.assertEqual(picking_in_01.move_lines.value, 1400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 700)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 350)
        # Distribucion 2 IN001 1000€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=1000)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        cost_line = distribution.cost_lines
        self.assertEqual(cost_line.product_qty, 4)
        self.assertEqual(cost_line.product_price_unit, 350)
        self.assertEqual(cost_line.standard_price_old, 350)
        self.assertEqual(cost_line.standard_price_new, 600)
        self.assertEqual(len(cost_line.expense_lines), 1)
        expense_line = cost_line.expense_lines
        self.assertEqual(expense_line.expense_amount, 1000)
        self.assertEqual(expense_line.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 4)
        self.assertEqual(distribution.total_purchase, 1400)
        self.assertEqual(distribution.total_expense, 1000)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 600)
        self.assertEqual(picking_in_01.move_lines.price_unit, 600)
        self.assertEqual(picking_in_01.move_lines.value, 2400)
        self.assertEqual(picking_out_01.move_lines.price_unit, -600)
        self.assertEqual(picking_out_01.move_lines.value, -600)
        self.assertEqual(picking_out_02.move_lines.price_unit, -600)
        self.assertEqual(picking_out_02.move_lines.value, -600)
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            1200)
        distribution.action_cancel()
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 700)
        self.assertEqual(self.product_tracking_lot.standard_price, 350)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 350)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 350)
        distribution.action_done()
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            1200)
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 600)
        self.assertEqual(picking_in_01.move_lines.price_unit, 600)
        self.assertEqual(picking_in_01.move_lines.value, 2400)
        self.assertEqual(picking_out_01.move_lines.price_unit, -600)
        self.assertEqual(picking_out_01.move_lines.value, -600)
        self.assertEqual(picking_out_02.move_lines.price_unit, -600)
        self.assertEqual(picking_out_02.move_lines.value, -600)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 600)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 600)
        # IN002 qty=2; price_unit=150; lot=002
        purchase_02 = self._create_purchase_order(
            self.product_tracking_lot, qty=2, price_unit=150)
        self.assertEqual(purchase_02.order_line[0].price_unit, 150)
        self.assertEqual(purchase_02.amount_untaxed, 300)
        self.assertEqual(len(purchase_02.picking_ids), 1)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02.move_line_ids[0].lot_id = lot_002.id
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 600)
        picking_in_02.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 600)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_02.move_lines.price_unit, 150)
        self.assertEqual(picking_in_02.move_lines.value, 300)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            1500)
        # OUT003 qty=2; price_unit=600€
        picking_out_03 = self._create_picking(
            'out', self.product_tracking_lot, qty=2)
        self.assertEqual(self.product_tracking_lot.standard_price, 150)
        self.assertEqual(picking_out_03.move_lines.price_unit, -600)
        self.assertEqual(picking_out_03.move_lines.value, -1200)
        self.assertEqual(picking_in_01.move_lines.price_unit, 600)
        self.assertEqual(picking_in_01.move_lines.value, 2400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        move_line_out_03 = picking_out_03.move_line_ids
        self.assertEquals(len(move_line_out_03.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_03.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_03.move_line_relation_ids.quantity, 2)
        self.assertEquals(
            move_line_out_03.move_line_relation_ids.price_unit, 600)
        # Distribucion 3 IN001 1000€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=1000)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        cost_line = distribution.cost_lines
        self.assertEqual(cost_line.product_qty, 4)
        self.assertEqual(cost_line.product_price_unit, 600)
        self.assertEqual(cost_line.standard_price_old, 600)
        self.assertEqual(cost_line.standard_price_new, 850)
        self.assertEqual(len(cost_line.expense_lines), 1)
        expense_line = cost_line.expense_lines
        self.assertEqual(expense_line.expense_amount, 1000)
        self.assertEqual(expense_line.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 4)
        self.assertEqual(distribution.total_purchase, 2400)
        self.assertEqual(distribution.total_expense, 1000)
        self.assertEqual(self.product_tracking_lot.standard_price, 150)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(self.product_tracking_lot.standard_price, 150)
        self.assertEqual(picking_in_01.move_lines.price_unit, 850)
        self.assertEqual(picking_in_01.move_lines.value, 3400)
        self.assertEqual(picking_out_01.move_lines.price_unit, -850)
        self.assertEqual(picking_out_01.move_lines.value, -850)
        self.assertEqual(picking_out_02.move_lines.price_unit, -850)
        self.assertEqual(picking_out_02.move_lines.value, -850)
        self.assertEqual(picking_out_03.move_lines.price_unit, - 850)
        self.assertEqual(picking_out_03.move_lines.value, -1700)

    def test_landed_cost_fifo_product_no_tracking_01(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # IN001 qty=2; price_unit=150€
        purchase_01 = self._create_purchase_order(
            self.product_no_tracking, qty=2, price_unit=150)
        self.assertEqual(purchase_01.order_line[0].price_unit, 150)
        self.assertEqual(purchase_01.amount_untaxed, 300)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 300)
        # IN002 qty=4; price_unit=100€
        purchase_02 = self._create_purchase_order(
            self.product_no_tracking, qty=4, price_unit=100)
        self.assertEqual(purchase_02.order_line[0].price_unit, 100)
        self.assertEqual(purchase_02.amount_untaxed, 400)
        self.assertEqual(len(purchase_02.picking_ids), 1)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        picking_in_02.action_done()
        time.sleep(1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 700)
        # OUT001 qty=3; price_unit=133.33€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(len(picking_out_01.move_line_ids), 1)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 3)
        self.assertEqual(
            round(picking_out_01.move_lines.price_unit, 2), -133.33)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -400)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 300)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_in_02 = picking_in_02.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01), 1)
        self.assertEquals(move_line_out_01.qty_done, 3)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_line_rel_1 = move_line_out_01.move_line_relation_ids[0]
        move_line_rel_2 = move_line_out_01.move_line_relation_ids[1]
        self.assertEqual(move_line_rel_1.move_line_id, move_line_in_01)
        self.assertEqual(move_line_rel_1.quantity, 2)
        self.assertEqual(move_line_rel_1.price_unit, 150)
        self.assertEqual(move_line_rel_2.move_line_id, move_line_in_02)
        self.assertEqual(move_line_rel_2.quantity, 1)
        self.assertEqual(move_line_rel_2.price_unit, 100)

    def test_landed_cost_fifo_product_no_tracking_02(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # IN001 qty=2; price_unit=150€
        purchase_01 = self._create_purchase_order(
            self.product_no_tracking, qty=2, price_unit=150)
        self.assertEqual(purchase_01.order_line[0].price_unit, 150)
        self.assertEqual(purchase_01.amount_untaxed, 300)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 300)
        # IN002 qty=4; price_unit=100€
        purchase_02 = self._create_purchase_order(
            self.product_no_tracking, qty=4, price_unit=100)
        self.assertEqual(purchase_02.order_line[0].price_unit, 100)
        self.assertEqual(purchase_02.amount_untaxed, 400)
        self.assertEqual(len(purchase_02.picking_ids), 1)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        picking_in_02.action_done()
        time.sleep(1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 700)
        # OUT001 qty=3; price_unit=133.33€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(len(picking_out_01.move_line_ids), 1)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 3)
        self.assertEqual(
            round(picking_out_01.move_lines.price_unit, 2), -133.33)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -400)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 300)
        # OUT002 qty=1; price_unit=100€
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=1)
        self.assertEqual(len(picking_out_02.move_line_ids), 1)
        self.assertEqual(picking_out_02.move_line_ids.qty_done, 1)
        self.assertEqual(picking_out_02.move_lines.price_unit, -100)
        self.assertEqual(picking_out_02.move_lines.product_uom_qty, 1)
        self.assertEqual(picking_out_02.move_lines.value, -100)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 200)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_in_02 = picking_in_02.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01), 1)
        self.assertEquals(move_line_out_01.qty_done, 3)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_line_rel_1 = move_line_out_01.move_line_relation_ids[0]
        move_line_rel_2 = move_line_out_01.move_line_relation_ids[1]
        self.assertEqual(move_line_rel_1.move_line_id, move_line_in_01)
        self.assertEqual(move_line_rel_1.quantity, 2)
        self.assertEqual(move_line_rel_1.price_unit, 150)
        self.assertEqual(move_line_rel_2.move_line_id, move_line_in_02)
        self.assertEqual(move_line_rel_2.quantity, 1)
        self.assertEqual(move_line_rel_2.price_unit, 100)

    def test_landed_cost_fifo_product_no_tracking_03(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # IN001 qty=2; price_unit=150€
        purchase_01 = self._create_purchase_order(
            self.product_no_tracking, qty=2, price_unit=150)
        self.assertEqual(purchase_01.order_line[0].price_unit, 150)
        self.assertEqual(purchase_01.amount_untaxed, 300)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 300)
        # IN002 qty=4; price_unit=100€
        purchase_02 = self._create_purchase_order(
            self.product_no_tracking, qty=4, price_unit=100)
        self.assertEqual(purchase_02.order_line[0].price_unit, 100)
        self.assertEqual(purchase_02.amount_untaxed, 400)
        self.assertEqual(len(purchase_02.picking_ids), 1)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        picking_in_02.action_done()
        time.sleep(1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 700)
        # OUT001 qty=3; price_unit=133.33€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(len(picking_out_01.move_line_ids), 1)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 3)
        self.assertEqual(
            round(picking_out_01.move_lines.price_unit, 2), -133.33)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -400)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 300)
        # OUT002 qty=1; price_unit=100€
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=1)
        self.assertEqual(len(picking_out_02.move_line_ids), 1)
        self.assertEqual(picking_out_02.move_line_ids.qty_done, 1)
        self.assertEqual(picking_out_02.move_lines.price_unit, -100)
        self.assertEqual(picking_out_02.move_lines.product_uom_qty, 1)
        self.assertEqual(picking_out_02.move_lines.value, -100)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 200)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_in_02 = picking_in_02.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01), 1)
        self.assertEquals(move_line_out_01.qty_done, 3)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_line_rel_1 = move_line_out_01.move_line_relation_ids[0]
        move_line_rel_2 = move_line_out_01.move_line_relation_ids[1]
        self.assertEqual(move_line_rel_1.move_line_id, move_line_in_01)
        self.assertEqual(move_line_rel_1.quantity, 2)
        self.assertEqual(move_line_rel_1.price_unit, 150)
        self.assertEqual(move_line_rel_2.move_line_id, move_line_in_02)
        self.assertEqual(move_line_rel_2.quantity, 1)
        self.assertEqual(move_line_rel_2.price_unit, 100)

    def test_landed_cost_fifo_product_no_tracking_04(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # IN001 qty=2; price_unit=150€
        purchase_01 = self._create_purchase_order(
            self.product_no_tracking, qty=2, price_unit=150)
        self.assertEqual(purchase_01.order_line[0].price_unit, 150)
        self.assertEqual(purchase_01.amount_untaxed, 300)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 300)
        # IN002 qty=4; price_unit=100€
        purchase_02 = self._create_purchase_order(
            self.product_no_tracking, qty=4, price_unit=100)
        self.assertEqual(purchase_02.order_line[0].price_unit, 100)
        self.assertEqual(purchase_02.amount_untaxed, 400)
        self.assertEqual(len(purchase_02.picking_ids), 1)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        picking_in_02.action_done()
        time.sleep(1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 700)
        # IN003 qty=10; price_unit=200€
        purchase_03 = self._create_purchase_order(
            self.product_no_tracking, qty=10, price_unit=200)
        self.assertEqual(purchase_03.order_line[0].price_unit, 200)
        self.assertEqual(purchase_03.amount_untaxed, 2000)
        self.assertEqual(len(purchase_03.picking_ids), 1)
        picking_in_03 = purchase_03.picking_ids
        picking_in_03.action_confirm()
        picking_in_03.action_assign()
        for move in picking_in_03.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        picking_in_03.action_done()
        time.sleep(1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_03.move_lines.quantity_done, 10)
        self.assertEqual(picking_in_03.move_lines.price_unit, 200)
        self.assertEqual(picking_in_03.move_lines.value, 2000)
        self.assertEqual(picking_in_03.move_lines.remaining_qty, 10)
        self.assertEqual(picking_in_03.move_lines.remaining_value, 2000)
        self.assertEqual(picking_in_03.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')),
            2700)
        # OUT001 qty=3; price_unit=133.33€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(len(picking_out_01.move_line_ids), 1)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 3)
        self.assertEqual(
            round(picking_out_01.move_lines.price_unit, 2), -133.33)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -400)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_03.move_lines.price_unit, 200)
        self.assertEqual(picking_in_03.move_lines.value, 2000)
        self.assertEqual(picking_in_03.move_lines.remaining_qty, 10)
        self.assertEqual(picking_in_03.move_lines.remaining_value, 2000)
        # OUT002 qty=1; price_unit=100€
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=1)
        self.assertEqual(len(picking_out_02.move_line_ids), 1)
        self.assertEqual(picking_out_02.move_line_ids.qty_done, 1)
        self.assertEqual(picking_out_02.move_lines.price_unit, -100)
        self.assertEqual(picking_out_02.move_lines.product_uom_qty, 1)
        self.assertEqual(picking_out_02.move_lines.value, -100)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 200)
        self.assertEqual(picking_in_03.move_lines.price_unit, 200)
        self.assertEqual(picking_in_03.move_lines.value, 2000)
        self.assertEqual(picking_in_03.move_lines.remaining_qty, 10)
        self.assertEqual(picking_in_03.move_lines.remaining_value, 2000)
        # OUT003 qty=9; price_unit=177.78€
        picking_out_03 = self._create_picking(
            'out', self.product_no_tracking, qty=9)
        self.assertEqual(len(picking_out_03.move_line_ids), 1)
        self.assertEqual(picking_out_03.move_line_ids.qty_done, 9)
        self.assertEqual(
            round(picking_out_03.move_lines.price_unit, 2), -177.78)
        self.assertEqual(picking_out_03.move_lines.product_uom_qty, 9)
        self.assertEqual(picking_out_03.move_lines.value, -1600)
        self.assertEqual(self.product_no_tracking.standard_price, 200)
        self.assertEqual(picking_in_01.move_lines.price_unit, 150)
        self.assertEqual(picking_in_01.move_lines.value, 300)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 100)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_03.move_lines.price_unit, 200)
        self.assertEqual(picking_in_03.move_lines.value, 2000)
        self.assertEqual(picking_in_03.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_03.move_lines.remaining_value, 600)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_in_02 = picking_in_02.move_line_ids
        move_line_in_03 = picking_in_03.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01), 1)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_line_rel_1 = move_line_out_01.move_line_relation_ids[0]
        move_line_rel_2 = move_line_out_01.move_line_relation_ids[1]
        self.assertEqual(move_line_rel_1.move_line_id, move_line_in_01)
        self.assertEqual(move_line_rel_1.quantity, 2)
        self.assertEqual(move_line_rel_1.price_unit, 150)
        self.assertEqual(move_line_rel_2.move_line_id, move_line_in_02)
        self.assertEqual(move_line_rel_2.quantity, 1)
        self.assertEqual(move_line_rel_2.price_unit, 100)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 100)
        move_line_out_03 = picking_out_03.move_line_ids
        self.assertEquals(len(move_line_out_03), 1)
        self.assertEquals(len(move_line_out_03.move_line_relation_ids), 2)
        move_line_rel_1 = move_line_out_03.move_line_relation_ids[0]
        move_line_rel_2 = move_line_out_03.move_line_relation_ids[1]
        self.assertEqual(move_line_rel_1.move_line_id, move_line_in_02)
        self.assertEqual(move_line_rel_1.quantity, 2)
        self.assertEqual(move_line_rel_1.price_unit, 100)
        self.assertEqual(move_line_rel_2.move_line_id, move_line_in_03)
        self.assertEqual(move_line_rel_2.quantity, 7)
        self.assertEqual(move_line_rel_2.price_unit, 200)

    def test_landed_cost_fifo_product_no_tracking_05(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # IN001 qty=4; price_unit=100
        purchase_01 = self._create_purchase_order(
            self.product_no_tracking, qty=4, price_unit=100)
        self.assertEqual(purchase_01.order_line[0].price_unit, 100)
        self.assertEqual(purchase_01.amount_untaxed, 400)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 400)
        # OUT001 qty=1; price_unit=100
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=1)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(picking_out_01.move_lines.price_unit, -100)
        self.assertEqual(picking_out_01.move_lines.value, -100)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        # Distribucion 1 IN001 1000€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=1000)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        cost_line = distribution.cost_lines
        self.assertEqual(cost_line.product_qty, 4)
        self.assertEqual(cost_line.product_price_unit, 100)
        self.assertEqual(cost_line.standard_price_old, 100)
        self.assertEqual(cost_line.standard_price_new, 350)
        self.assertEqual(len(cost_line.expense_lines), 1)
        expense_line = cost_line.expense_lines
        self.assertEqual(expense_line.expense_amount, 1000)
        self.assertEqual(expense_line.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 4)
        self.assertEqual(distribution.total_purchase, 400)
        self.assertEqual(distribution.total_expense, 1000)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_no_tracking.standard_price, 350)
        self.assertEqual(picking_in_01.move_lines.price_unit, 350)
        self.assertEqual(picking_in_01.move_lines.value, 1400)
        self.assertEqual(picking_out_01.move_lines.price_unit, -350)
        self.assertEqual(picking_out_01.move_lines.value, -350)
        move_line_in_01 = picking_in_01.move_line_ids
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 350)
        # OUT002 qty=1; price_unit=350
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=1)
        self.assertEqual(self.product_no_tracking.standard_price, 350)
        self.assertEqual(picking_out_02.move_lines.price_unit, -350)
        self.assertEqual(picking_out_02.move_lines.value, -350)
        self.assertEqual(picking_in_01.move_lines.price_unit, 350)
        self.assertEqual(picking_in_01.move_lines.value, 1400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 700)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 350)
        # Distribucion 2 IN001 1000€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=1000)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        cost_line = distribution.cost_lines
        self.assertEqual(cost_line.product_qty, 4)
        self.assertEqual(cost_line.product_price_unit, 350)
        self.assertEqual(cost_line.standard_price_old, 350)
        self.assertEqual(cost_line.standard_price_new, 600)
        self.assertEqual(len(cost_line.expense_lines), 1)
        expense_line = cost_line.expense_lines
        self.assertEqual(expense_line.expense_amount, 1000)
        self.assertEqual(expense_line.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 4)
        self.assertEqual(distribution.total_purchase, 1400)
        self.assertEqual(distribution.total_expense, 1000)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_no_tracking.standard_price, 600)
        self.assertEqual(picking_in_01.move_lines.price_unit, 600)
        self.assertEqual(picking_in_01.move_lines.value, 2400)
        self.assertEqual(picking_out_01.move_lines.price_unit, -600)
        self.assertEqual(picking_out_01.move_lines.value, -600)
        self.assertEqual(picking_out_02.move_lines.price_unit, -600)
        self.assertEqual(picking_out_02.move_lines.value, -600)
        # IN002 qty=2; price_unit=150
        purchase_02 = self._create_purchase_order(
            self.product_no_tracking, qty=2, price_unit=150)
        self.assertEqual(purchase_02.order_line[0].price_unit, 150)
        self.assertEqual(purchase_02.amount_untaxed, 300)
        self.assertEqual(len(purchase_02.picking_ids), 1)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_no_tracking.standard_price, 600)
        picking_in_02.action_done()
        time.sleep(1)
        self.assertEqual(self.product_no_tracking.standard_price, 600)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 2)
        self.assertEqual(picking_in_02.move_lines.price_unit, 150)
        self.assertEqual(picking_in_02.move_lines.value, 300)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 2)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 300)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')),
            1500)
        # OUT003 qty=2; price_unit=600
        picking_out_03 = self._create_picking(
            'out', self.product_no_tracking, qty=2)
        self.assertEqual(self.product_no_tracking.standard_price, 150)
        self.assertEqual(picking_out_03.move_lines.price_unit, -600)
        self.assertEqual(picking_out_03.move_lines.value, -1200)
        self.assertEqual(picking_in_01.move_lines.price_unit, 600)
        self.assertEqual(picking_in_01.move_lines.value, 2400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        move_line_out_03 = picking_out_03.move_line_ids
        self.assertEquals(len(move_line_out_03.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_03.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_03.move_line_relation_ids.quantity, 2)
        self.assertEquals(
            move_line_out_03.move_line_relation_ids.price_unit, 600)
        # Distribucion 3 IN001 1000€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=1000)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        cost_line = distribution.cost_lines
        self.assertEqual(cost_line.product_qty, 4)
        self.assertEqual(cost_line.product_price_unit, 600)
        self.assertEqual(cost_line.standard_price_old, 600)
        self.assertEqual(cost_line.standard_price_new, 850)
        self.assertEqual(len(cost_line.expense_lines), 1)
        expense_line = cost_line.expense_lines
        self.assertEqual(expense_line.expense_amount, 1000)
        self.assertEqual(expense_line.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 4)
        self.assertEqual(distribution.total_purchase, 2400)
        self.assertEqual(distribution.total_expense, 1000)
        self.assertEqual(self.product_no_tracking.standard_price, 150)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(self.product_no_tracking.standard_price, 150)
        self.assertEqual(picking_in_01.move_lines.price_unit, 850)
        self.assertEqual(picking_in_01.move_lines.value, 3400)
        self.assertEqual(picking_out_01.move_lines.price_unit, -850)
        self.assertEqual(picking_out_01.move_lines.value, -850)
        self.assertEqual(picking_out_02.move_lines.price_unit, -850)
        self.assertEqual(picking_out_02.move_lines.value, -850)
        self.assertEqual(picking_out_03.move_lines.price_unit, -850)
        self.assertEqual(picking_out_03.move_lines.value, -1700)

    def test_landed_cost_fifo_product_tracking_lot_inventory_01(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # Inventory adjustment qty=1; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 1, lot_001)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_tracking_lot.stock_value, 1.0)
        self.assertEqual(self.product_tracking_lot.standard_price, 1.0)
        # IN001 qty=5; price_unit=100€; lot=001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 5)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 5)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 500)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 501)
        # OUT001 qty=1, price_unit=1€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 1)
        self.assertEqual(picking_out_01.move_line_ids.lot_id, lot_001)
        self.assertEqual(picking_out_01.move_lines.price_unit, -1)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 1)
        self.assertEqual(picking_out_01.move_lines.value, -1)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 5)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 500)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_inventory_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 1)

    def test_landed_cost_fifo_product_tracking_lot_inventory_02(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # Inventory adjustment qty=1; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 1, lot_001)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_tracking_lot.stock_value, 1.0)
        self.assertEqual(self.product_tracking_lot.standard_price, 1.0)
        # IN001 qty=5; price_unit=100€; lot=001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 5)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 5)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 500)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 501)
        # OUT001 qty=3, price_unit=67€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 3)
        self.assertEqual(picking_out_01.move_line_ids.lot_id, lot_001)
        self.assertEqual(picking_out_01.move_lines.price_unit, -67)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -201)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 1)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)

    def test_landed_cost_fifo_product_tracking_lot_inventory_03(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # Inventory adjustment qty=1; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 1, lot_001)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_tracking_lot.stock_value, 1.0)
        self.assertEqual(self.product_tracking_lot.standard_price, 1.0)
        # IN001 qty=5; price_unit=100€; lot=001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 5)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 5)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 500)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 501)
        # OUT001 qty=3, price_unit=67€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 3)
        self.assertEqual(picking_out_01.move_line_ids.lot_id, lot_001)
        self.assertEqual(picking_out_01.move_lines.price_unit, -67)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -201)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 1)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        # Inventory adjustment 2 qty=10; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 10, lot_001)
        move_line_inventory_02 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_02), 1)
        self.assertEqual(move_line_inventory_02.qty_done, 7)
        self.assertEquals(self.product_tracking_lot.with_context(
            location=self.stock_location.id).qty_available, 10)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(self.product_tracking_lot.stock_value, 1000)
        # OUT002 qty=4, price_unit=100€
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=4)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(picking_out_02.move_line_ids.qty_done, 4)
        self.assertEqual(picking_out_02.move_line_ids.lot_id, lot_001)
        self.assertEqual(picking_out_02.move_lines.price_unit, -100)
        self.assertEqual(picking_out_02.move_lines.product_uom_qty, 4)
        self.assertEqual(picking_out_02.move_lines.value, -400)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        move_lines_out_01 = picking_out_02.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 3))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_inventory_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)

    def test_landed_cost_fifo_product_tracking_lot_inventory_04(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # Inventory adjustment qty=1; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 1, lot_001)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_tracking_lot.stock_value, 1.0)
        self.assertEqual(self.product_tracking_lot.standard_price, 1.0)
        # IN001 qty=5; price_unit=100€; lot=001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 5)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 5)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 500)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 501)
        # IN002 qty=4; price_unit=200€; lot=002
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02 = self._create_picking(
            'in', self.product_tracking_lot, qty=4, price_unit=200,
            lot=lot_002)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_02.move_lines.price_unit, 200)
        self.assertEqual(picking_in_02.move_lines.value, 800)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 800)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            1301)
        # OUT001 qty=3, price_unit=67€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 3)
        self.assertEqual(picking_out_01.move_line_ids.lot_id, lot_001)
        self.assertEqual(picking_out_01.move_lines.price_unit, -67)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -201)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 1)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        # Inventory adjustment 2 qty=10; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 10, lot_001)
        move_line_inventory_02 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_02), 1)
        self.assertEqual(move_line_inventory_02.qty_done, 7)
        self.assertEquals(self.product_tracking_lot.with_context(
            location=self.stock_location.id, lot_id=lot_001.id).qty_available,
            10)
        self.assertEquals(self.product_tracking_lot.with_context(
            location=self.stock_location.id, lot_id=lot_002.id).qty_available,
            4)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(self.product_tracking_lot.stock_value, 1800)
        # OUT002 qty=4 price_unit=
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=4)
        self.assertEqual(self.product_tracking_lot.standard_price, 200)
        self.assertEqual(picking_out_02.move_line_ids.qty_done, 4)
        self.assertEqual(picking_out_02.move_line_ids.lot_id, lot_001)
        self.assertEqual(picking_out_02.move_lines.price_unit, -125)
        self.assertEqual(picking_out_02.move_lines.product_uom_qty, 4)
        self.assertEqual(picking_out_02.move_lines.value, -500)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        move_lines_out_01 = picking_out_02.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 3))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_inventory_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        self.assertEqual(self.product_tracking_lot.standard_price, 200)

    def test_landed_cost_fifo_product_no_tracking_inventory_01(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # Inventory adjustment qty=1
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 1)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_no_tracking.stock_value, 1.0)
        self.assertEqual(self.product_no_tracking.standard_price, 1.0)
        # IN001 qty=5; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 5)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 5)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 500)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 501)
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=1; price_unit=1€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=1)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 1)
        self.assertFalse(picking_out_01.move_line_ids.lot_id)
        self.assertEqual(picking_out_01.move_lines.price_unit, -1)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 1)
        self.assertEqual(picking_out_01.move_lines.value, -1)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 5)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 500)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_inventory_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 1)

    def test_landed_cost_fifo_product_no_tracking_inventory_02(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # Inventory adjustment qty=1
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 1)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_no_tracking.stock_value, 1.0)
        self.assertEqual(self.product_no_tracking.standard_price, 1.0)
        # IN001 qty=5; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 5)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 5)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 500)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 501)
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=3; price_unit=67
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 3)
        self.assertFalse(picking_out_01.move_line_ids.lot_id)
        self.assertEqual(picking_out_01.move_lines.price_unit, -67)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -201)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01), 1)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_line_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 1)
        move_line_out_relation_01_02 = (
            move_line_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)

    def test_landed_cost_fifo_product_no_tracking_inventory_03(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # Inventory adjustment qty=1
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 1)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_no_tracking.stock_value, 1.0)
        self.assertEqual(self.product_no_tracking.standard_price, 1.0)
        # IN001 qty=5; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 5)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 5)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 500)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 501)
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=3; price_unit=67€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 3)
        self.assertFalse(picking_out_01.move_line_ids.lot_id)
        self.assertEqual(picking_out_01.move_lines.price_unit, -67)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -201)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01), 1)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_line_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 1)
        move_line_out_relation_01_02 = (
            move_line_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        # Inventory adjustment 2 qty=10
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 10)
        move_line_inventory_02 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_02), 1)
        self.assertEqual(move_line_inventory_02.qty_done, 7)
        self.assertEquals(self.product_no_tracking.with_context(
            location=self.stock_location.id).qty_available, 10)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(self.product_no_tracking.stock_value, 1000)
        # OUT002 qty=4; price_unit=100€
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=4)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(picking_out_02.move_line_ids.qty_done, 4)
        self.assertFalse(picking_out_02.move_line_ids.lot_id)
        self.assertEqual(picking_out_02.move_lines.price_unit, -100)
        self.assertEqual(picking_out_02.move_lines.product_uom_qty, 4)
        self.assertEqual(picking_out_02.move_lines.value, -400)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        move_lines_out_01 = picking_out_02.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 3))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_inventory_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        self.assertEqual(self.product_no_tracking.standard_price, 100)

    def test_landed_cost_fifo_product_no_tracking_inventory_04(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # Inventory adjustment qty=1
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 1)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_no_tracking.stock_value, 1.0)
        self.assertEqual(self.product_no_tracking.standard_price, 1.0)
        # IN001 qty=5; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 5)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 5)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 500)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 501)
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=4; price_unit=200€
        picking_in_02 = self._create_picking(
            'in', self.product_no_tracking, qty=4, price_unit=200)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        self.assertEqual(picking_in_02.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_02.move_lines.price_unit, 200)
        self.assertEqual(picking_in_02.move_lines.value, 800)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 800)
        self.assertEqual(picking_in_02.state, 'done')
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 1301)
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT001 qty=3; price_unit=67€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 3)
        self.assertFalse(picking_out_01.move_line_ids.lot_id)
        self.assertEqual(picking_out_01.move_lines.price_unit, -67)
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 3)
        self.assertEqual(picking_out_01.move_lines.value, -201)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 300)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01), 1)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_line_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 1)
        move_line_out_relation_01_02 = (
            move_line_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        # Inventory adjustment 2 qty=10
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 10)
        move_line_inventory_02 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_02), 1)
        self.assertEqual(move_line_inventory_02.qty_done, 3)
        self.assertEquals(self.product_no_tracking.with_context(
            location=self.stock_location.id).qty_available, 10)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(self.product_no_tracking.stock_value, 1400)
        # OUT002 qty=4; price_unit=125€
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=4)
        self.assertEqual(self.product_no_tracking.standard_price, 200)
        self.assertEqual(picking_out_02.move_line_ids.qty_done, 4)
        self.assertFalse(picking_out_02.move_line_ids.lot_id)
        self.assertEqual(picking_out_02.move_lines.price_unit, -125)
        self.assertEqual(picking_out_02.move_lines.product_uom_qty, 4)
        self.assertEqual(picking_out_02.move_lines.value, -500)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 500)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 0)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 0)
        self.assertEqual(picking_in_02.move_lines.price_unit, 200)
        self.assertEqual(picking_in_02.move_lines.value, 800)
        self.assertEqual(picking_in_02.move_lines.remaining_qty, 3)
        self.assertEqual(picking_in_02.move_lines.remaining_value, 600)
        move_lines_out_01 = picking_out_02.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 3))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 200)
        self.assertEqual(self.product_no_tracking.standard_price, 200)

    def test_landed_cost_fifo_distribution_with_several_cost_lines(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # IN001
        #   - product_tracking_lot: qty=4; price_unit=100; lot=001
        #   - product_no_tracking:  qty=1; price_unit=600
        purchase_01 = self._create_record(
            model_name='purchase.order',
            vals={
                'partner_id': self.supplier.id,
                'order_line': [
                    (0, 0, {
                        'product_id': self.product_tracking_lot.id,
                        'product_qty': 4,
                        'name': self.product_tracking_lot.name,
                        'product_uom': self.product_tracking_lot.uom_id.id,
                        'price_unit': 100,
                        'date_planned': fields.Datetime.now(),
                    }),
                    (0, 0, {
                        'product_id': self.product_no_tracking.id,
                        'product_qty': 1,
                        'name': self.product_no_tracking.name,
                        'product_uom': self.product_no_tracking.uom_id.id,
                        'price_unit': 600,
                        'date_planned': fields.Datetime.now(),
                    }),
                ],
            },
        )
        purchase_01.button_confirm()
        self.assertEqual(purchase_01.amount_untaxed, 1000)
        self.assertEqual(len(purchase_01.picking_ids), 1)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01.move_line_ids[0].lot_id = lot_001.id
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        picking_in_01.action_done()
        time.sleep(1)
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(self.product_no_tracking.standard_price, 1)
        move_in_01_product_tracking_lot = picking_in_01.move_lines.filtered(
            lambda ml: ml.product_id == self.product_tracking_lot)
        self.assertEqual(move_in_01_product_tracking_lot.quantity_done, 4)
        self.assertEqual(move_in_01_product_tracking_lot.price_unit, 100)
        self.assertEqual(move_in_01_product_tracking_lot.value, 400)
        self.assertEqual(move_in_01_product_tracking_lot.remaining_qty, 4)
        self.assertEqual(move_in_01_product_tracking_lot.remaining_value, 400)
        move_in_01_product_no_tracking = picking_in_01.move_lines.filtered(
            lambda ml: ml.product_id == self.product_no_tracking)
        self.assertEqual(move_in_01_product_no_tracking.quantity_done, 1)
        self.assertEqual(move_in_01_product_no_tracking.price_unit, 600)
        self.assertEqual(move_in_01_product_no_tracking.value, 600)
        self.assertEqual(move_in_01_product_no_tracking.remaining_qty, 1)
        self.assertEqual(move_in_01_product_no_tracking.remaining_value, 600)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 400)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 600)
        # OUT001 product_tracking_lot qty=1; price_unit=100
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(picking_out_01.move_lines.price_unit, -100)
        self.assertEqual(picking_out_01.move_lines.value, -100)
        self.assertEqual(move_in_01_product_tracking_lot.price_unit, 100)
        self.assertEqual(move_in_01_product_tracking_lot.value, 400)
        self.assertEqual(move_in_01_product_tracking_lot.remaining_qty, 3)
        self.assertEqual(move_in_01_product_tracking_lot.remaining_value, 300)
        move_line_in_01_product_tracking_lot = (
            move_in_01_product_tracking_lot.move_line_ids)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01_product_tracking_lot)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        # OUT002 product_no_tracking qty=1; price_unit=600
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=1)
        self.assertEqual(self.product_no_tracking.standard_price, 600)
        self.assertEqual(picking_out_02.move_lines.price_unit, -600)
        self.assertEqual(picking_out_02.move_lines.value, -600)
        self.assertEqual(move_in_01_product_no_tracking.price_unit, 600)
        self.assertEqual(move_in_01_product_no_tracking.value, 600)
        self.assertEqual(move_in_01_product_no_tracking.remaining_qty, 0)
        self.assertEqual(move_in_01_product_no_tracking.remaining_value, 0)
        move_line_in_01_product_no_tracking = (
            move_in_01_product_no_tracking.move_line_ids)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_01_product_no_tracking)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 600)
        # Distribucion 1 IN001 1000€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=1000)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 2)
        cost_line_product_tracking_lot = distribution.cost_lines.filtered(
            lambda ln: ln.product_id == self.product_tracking_lot)
        self.assertEqual(cost_line_product_tracking_lot.product_qty, 4)
        self.assertEqual(
            cost_line_product_tracking_lot.product_price_unit, 100)
        self.assertEqual(
            cost_line_product_tracking_lot.standard_price_old, 100)
        self.assertEqual(
            cost_line_product_tracking_lot.standard_price_new, 200)
        self.assertEqual(len(cost_line_product_tracking_lot.expense_lines), 1)
        cost_line_product_no_tracking = distribution.cost_lines.filtered(
            lambda ln: ln.product_id == self.product_no_tracking)
        self.assertEqual(cost_line_product_no_tracking.product_qty, 1)
        self.assertEqual(cost_line_product_no_tracking.product_price_unit, 600)
        self.assertEqual(cost_line_product_no_tracking.standard_price_old, 600)
        self.assertEqual(
            cost_line_product_no_tracking.standard_price_new, 1200)
        self.assertEqual(len(cost_line_product_no_tracking.expense_lines), 1)
        expense_line_cost_line_product_tracking_lot = (
            cost_line_product_tracking_lot.expense_lines)
        self.assertEqual(
            expense_line_cost_line_product_tracking_lot.expense_amount, 400)
        self.assertEqual(
            expense_line_cost_line_product_tracking_lot.cost_ratio, 100)
        expense_line_cost_line_product_no_tracking = (
            cost_line_product_no_tracking.expense_lines)
        self.assertEqual(
            expense_line_cost_line_product_no_tracking.expense_amount, 600)
        self.assertEqual(
            expense_line_cost_line_product_no_tracking.cost_ratio, 600)
        self.assertEqual(distribution.total_uom_qty, 5)
        self.assertEqual(distribution.total_purchase, 1000)
        self.assertEqual(distribution.total_expense, 1000)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 200)
        self.assertEqual(move_in_01_product_tracking_lot.price_unit, 200)
        self.assertEqual(move_in_01_product_tracking_lot.value, 800)
        self.assertEqual(picking_out_01.move_lines.price_unit, -200)
        self.assertEqual(picking_out_01.move_lines.value, -200)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01_product_tracking_lot)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 200)
        self.assertEqual(self.product_no_tracking.standard_price, 600)
        self.assertEqual(move_in_01_product_no_tracking.price_unit, 1200)
        self.assertEqual(move_in_01_product_no_tracking.value, 1200)
        self.assertEqual(picking_out_02.move_lines.price_unit, -1200)
        self.assertEqual(picking_out_02.move_lines.value, -1200)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_01_product_no_tracking)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 1200)
        distribution.action_cancel()
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(picking_out_01.move_lines.price_unit, -100)
        self.assertEqual(picking_out_01.move_lines.value, -100)
        self.assertEqual(move_in_01_product_tracking_lot.price_unit, 100)
        self.assertEqual(move_in_01_product_tracking_lot.value, 400)
        self.assertEqual(move_in_01_product_tracking_lot.remaining_qty, 3)
        self.assertEqual(move_in_01_product_tracking_lot.remaining_value, 300)
        move_line_in_01_product_tracking_lot = (
            move_in_01_product_tracking_lot.move_line_ids)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01_product_tracking_lot)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        self.assertEqual(self.product_no_tracking.standard_price, 600)
        self.assertEqual(picking_out_02.move_lines.price_unit, -600)
        self.assertEqual(picking_out_02.move_lines.value, -600)
        self.assertEqual(move_in_01_product_no_tracking.price_unit, 600)
        self.assertEqual(move_in_01_product_no_tracking.value, 600)
        self.assertEqual(move_in_01_product_no_tracking.remaining_qty, 0)
        self.assertEqual(move_in_01_product_no_tracking.remaining_value, 0)
        move_line_in_01_product_no_tracking = (
            move_in_01_product_no_tracking.move_line_ids)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_01_product_no_tracking)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 600)

    def test_landed_cost_fifo_product_tracking_lot_several_outs(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        # IN000 qty=1; price_unit=14€; lot=000
        purchase_00 = self._create_purchase_order(
            self.product_tracking_lot, qty=1, price_unit=14)
        picking_in_00 = purchase_00.picking_ids
        picking_in_00.action_confirm()
        picking_in_00.action_assign()
        lot_000 = self.env['stock.production.lot'].create({
            'name': '000',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_00.move_line_ids[0].lot_id = lot_000.id
        for move in picking_in_00.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_in_00.action_done()
        time.sleep(1)
        # IN001 qty=4; price_unit=100€; lot=001
        purchase_01 = self._create_purchase_order(
            self.product_tracking_lot, qty=4, price_unit=100)
        picking_in_01 = purchase_01.picking_ids
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01.move_line_ids[0].lot_id = lot_001.id
        for move in picking_in_01.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_in_01.action_done()
        time.sleep(1)
        # IN002 qty=2; price_unit=30€; lot=002
        purchase_02 = self._create_purchase_order(
            self.product_tracking_lot, qty=2, price_unit=30)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02.move_line_ids[0].lot_id = lot_002.id
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_in_02.action_done()
        time.sleep(1)
        # OUT001 qty=6; price_unit=444€/6=74€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=6)
        # Distribucion 1 IN001 1408€
        distribution = self._create_record(
            model_name='purchase.cost.distribution',
            vals={},
        )
        invoice = self._create_invoice(self.cost, qty=1, price_unit=1408)
        invoice_wizard = self.env['import.invoice.line.wizard'].with_context(
            active_id=distribution.id)
        invoice_wizard = invoice_wizard.create({
            'supplier': self.supplier.id,
            'invoice': invoice.id,
            'invoice_line': invoice.invoice_line_ids.id,
            'expense_type': self.type_amount.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 1)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 30)
        self.assertEqual(picking_in_01.move_lines.price_unit, 452)
        self.assertEqual(picking_in_01.move_lines.value, 1808)
        # self.assertAlmostEqual(
        # picking_out_01.move_lines.price_unit, -308.66, places=2)
        self.assertEqual(
            round(picking_out_01.move_lines.price_unit, 2), -308.67)
        self.assertEqual(picking_out_01.move_lines.value, -1852)
