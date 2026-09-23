###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestUnitOfMeasureDifferents(TransactionCase):

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
        self.type_weight = self._create_record(
            model_name='purchase.expense.type',
            vals={
                'name': 'Weight',
                'calculation_method': 'weight',
            },
        )
        self.type_volume = self._create_record(
            model_name='purchase.expense.type',
            vals={
                'name': 'Volume',
                'calculation_method': 'volume',
            },
        )
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.uom_m3 = self.env['uom.uom'].create({
            'name': 'm³',
            'category_id': self.env.ref('uom.product_uom_categ_vol').id,
            'factor_inv': 1000,
            'uom_type': 'bigger',
        })

    def _create_record(self, model_name, vals):
        record = self._create_vals(model_name, vals)
        return record.create(record._convert_to_write(record._cache))

    def _create_vals(self, model_name, vals):
        model = self.env[model_name]
        data = model.default_get(list(model.fields_get()))
        data.update(vals)
        return model.new(data)

    def _create_picking(self, in_or_out, product, qty, price_unit, lot=None):
        if in_or_out == 'in':
            location_src = self.env.ref('stock.stock_location_suppliers')
            location_dst = self.stock_location
            sign_price = 1
        elif in_or_out == 'out':
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
            'price_unit': sign_price * price_unit,
            'value': sign_price * qty * price_unit,
            # @TODO En el mrp_cost_price puede estar mal, esto no
            # se reseteaba a draft, y si no lo está, el método
            # product_price_update_before_done no hace nada de
            # actualizar el precio de coste
            # addons/stock_account/models/stock.py:435
            'state': 'draft',
        }
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
        return inventory

    def test_landed_cost_uom_differents(self):
        self.product_tracking_lot.weight = 2000
        self.product_tracking_lot.weight_uom_id = self.env.ref(
            'uom.product_uom_gram').id
        self.product_tracking_lot.volume = 1
        self.product_tracking_lot.volume_uom_id = self.uom_m3.id
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        # IN001 qty=4; price_unit=100; lot=001
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
        self.assertEqual(self.product_tracking_lot.standard_price, 1)
        self.assertEqual(picking_in_01.move_lines.quantity_done, 4)
        self.assertEqual(picking_in_01.move_lines.price_unit, 100)
        self.assertEqual(picking_in_01.move_lines.value, 400)
        self.assertEqual(picking_in_01.move_lines.remaining_qty, 4)
        self.assertEqual(picking_in_01.move_lines.remaining_value, 400)
        self.assertEqual(picking_in_01.state, 'done')
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 400)
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
            'expense_type': self.type_weight.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, picking_in_01.ids)],
        })
        picking_wizard.action_import_picking()
        self.assertEqual(distribution.cost_lines[0].total_volume, 4000)
        self.assertEqual(distribution.cost_lines[0].total_weight, 8)
        self.assertEqual(distribution.total_volume, 4000)
        self.assertEqual(distribution.total_weight, 8)
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
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            1400)
        distribution.action_cancel()
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 400)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 350)
        self.assertEqual(picking_in_01.move_lines.price_unit, 350)
        self.assertEqual(picking_in_01.move_lines.value, 1400)

    def test_landed_cost_uom_differents_weight_expense_type(self):
        self.product_tracking_lot.weight = 2000
        self.product_tracking_lot.weight_uom_id = self.env.ref(
            'uom.product_uom_gram').id
        self.product_tracking_lot.volume = 1
        self.product_tracking_lot.volume_uom_id = self.uom_m3.id
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        self.product_no_tracking.weight = 1000
        self.product_no_tracking.weight_uom_id = self.env.ref(
            'uom.product_uom_gram').id
        self.product_no_tracking.volume = 1
        self.product_no_tracking.volume_uom_id = self.uom_m3.id
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # IN001 qty=4; price_unit=100; lot=001
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
        # IN002 qty=2; price_unit=100; lot=
        purchase_02 = self._create_purchase_order(
            self.product_no_tracking, qty=2, price_unit=100)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_in_02.action_done()
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
            'expense_type': self.type_weight.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, [picking_in_01.id, picking_in_02.id])],
        })
        picking_wizard.action_import_picking()
        cost_line_tracking = distribution.cost_lines.filtered(
            lambda ln: ln.product_id == self.product_tracking_lot)
        self.assertEqual(cost_line_tracking.total_volume, 4000)
        self.assertEqual(cost_line_tracking.total_weight, 8)
        cost_line_no_tracking = distribution.cost_lines.filtered(
            lambda ln: ln.product_id == self.product_no_tracking)
        self.assertEqual(cost_line_no_tracking.total_volume, 2000)
        self.assertEqual(cost_line_no_tracking.total_weight, 2)
        self.assertEqual(distribution.total_volume, 6000)
        self.assertEqual(distribution.total_weight, 10)
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 2)
        self.assertEqual(cost_line_tracking.product_qty, 4)
        self.assertEqual(cost_line_tracking.product_price_unit, 100)
        self.assertEqual(cost_line_tracking.standard_price_old, 100)
        self.assertEqual(cost_line_tracking.standard_price_new, 300)
        self.assertEqual(len(cost_line_tracking.expense_lines), 1)
        expense_line_tracking = cost_line_tracking.expense_lines
        self.assertEqual(expense_line_tracking.expense_amount, 800)
        self.assertEqual(expense_line_tracking.cost_ratio, 200)
        self.assertEqual(cost_line_no_tracking.product_qty, 2)
        self.assertEqual(cost_line_no_tracking.product_price_unit, 100)
        self.assertEqual(cost_line_no_tracking.standard_price_old, 100)
        self.assertEqual(cost_line_no_tracking.standard_price_new, 200)
        self.assertEqual(len(cost_line_no_tracking.expense_lines), 1)
        expense_line_no_tracking = cost_line_no_tracking.expense_lines
        self.assertEqual(expense_line_no_tracking.expense_amount, 200)
        self.assertEqual(expense_line_no_tracking.cost_ratio, 100)
        self.assertEqual(distribution.total_uom_qty, 6)
        self.assertEqual(distribution.total_purchase, 600)
        self.assertEqual(distribution.total_expense, 1000)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 300)
        self.assertEqual(self.product_no_tracking.standard_price, 200)
        self.assertEqual(picking_in_01.move_lines.price_unit, 300)
        self.assertEqual(picking_in_01.move_lines.value, 1200)
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            1200)
        self.assertEqual(picking_in_02.move_lines.price_unit, 200)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')),
            400)
        distribution.action_cancel()
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 400)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 200)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 300)
        self.assertEqual(self.product_no_tracking.standard_price, 200)
        self.assertEqual(picking_in_01.move_lines.price_unit, 300)
        self.assertEqual(picking_in_01.move_lines.value, 1200)
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            1200)
        self.assertEqual(picking_in_02.move_lines.price_unit, 200)
        self.assertEqual(picking_in_02.move_lines.value, 400)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')),
            400)

    def test_landed_cost_uom_differents_volume_expense_type(self):
        self.product_tracking_lot.weight = 2000
        self.product_tracking_lot.weight_uom_id = self.env.ref(
            'uom.product_uom_gram').id
        self.product_tracking_lot.volume = 1
        self.product_tracking_lot.volume_uom_id = self.uom_m3.id
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.product_tracking_lot.standard_price = 1
        self.product_no_tracking.weight = 1000
        self.product_no_tracking.weight_uom_id = self.env.ref(
            'uom.product_uom_gram').id
        self.product_no_tracking.volume = 2
        self.product_no_tracking.volume_uom_id = self.uom_m3.id
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.product_no_tracking.standard_price = 1
        # IN001 qty=4; price_unit=100; lot=001
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
        # IN002 qty=2; price_unit=100; lot=
        purchase_02 = self._create_purchase_order(
            self.product_no_tracking, qty=2, price_unit=100)
        picking_in_02 = purchase_02.picking_ids
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        for move in picking_in_02.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_in_02.action_done()
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
            'expense_type': self.type_volume.id,
        })
        invoice_wizard.action_import_invoice_line()
        picking_wizard = self.env['picking.import.wizard'].with_context(
            active_id=distribution.id)
        picking_wizard = picking_wizard.create({
            'supplier': self.supplier.id,
            'pickings': [(6, 0, [picking_in_01.id, picking_in_02.id])],
        })
        picking_wizard.action_import_picking()
        cost_line_tracking = distribution.cost_lines.filtered(
            lambda ln: ln.product_id == self.product_tracking_lot)
        self.assertEqual(cost_line_tracking.total_volume, 4000)
        self.assertEqual(cost_line_tracking.total_weight, 8)
        cost_line_no_tracking = distribution.cost_lines.filtered(
            lambda ln: ln.product_id == self.product_no_tracking)
        self.assertEqual(cost_line_no_tracking.total_volume, 4000)
        self.assertEqual(cost_line_no_tracking.total_weight, 2)
        self.assertEqual(distribution.total_volume, 8000)
        self.assertEqual(distribution.total_weight, 10)
        self.assertEqual(distribution.state, 'draft')
        distribution.action_calculate()
        self.assertEqual(distribution.state, 'calculated')
        self.assertEqual(len(distribution.cost_lines.ids), 2)
        self.assertEqual(cost_line_tracking.product_qty, 4)
        self.assertEqual(cost_line_tracking.product_price_unit, 100)
        self.assertEqual(cost_line_tracking.standard_price_old, 100)
        self.assertEqual(cost_line_tracking.standard_price_new, 225)
        self.assertEqual(len(cost_line_tracking.expense_lines), 1)
        expense_line_tracking = cost_line_tracking.expense_lines
        self.assertEqual(expense_line_tracking.expense_amount, 500)
        self.assertEqual(expense_line_tracking.cost_ratio, 125)
        self.assertEqual(cost_line_no_tracking.product_qty, 2)
        self.assertEqual(cost_line_no_tracking.product_price_unit, 100)
        self.assertEqual(cost_line_no_tracking.standard_price_old, 100)
        self.assertEqual(cost_line_no_tracking.standard_price_new, 350)
        self.assertEqual(len(cost_line_no_tracking.expense_lines), 1)
        expense_line_no_tracking = cost_line_no_tracking.expense_lines
        self.assertEqual(expense_line_no_tracking.expense_amount, 500)
        self.assertEqual(expense_line_no_tracking.cost_ratio, 250)
        self.assertEqual(distribution.total_uom_qty, 6)
        self.assertEqual(distribution.total_purchase, 600)
        self.assertEqual(distribution.total_expense, 1000)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 225)
        self.assertEqual(self.product_no_tracking.standard_price, 350)
        self.assertEqual(picking_in_01.move_lines.price_unit, 225)
        self.assertEqual(picking_in_01.move_lines.value, 900)
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            900)
        self.assertEqual(picking_in_02.move_lines.price_unit, 350)
        self.assertEqual(picking_in_02.move_lines.value, 700)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')),
            700)
        distribution.action_cancel()
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')), 400)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')), 200)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        distribution.action_done()
        self.assertEqual(distribution.state, 'done')
        self.assertEqual(self.product_tracking_lot.standard_price, 225)
        self.assertEqual(self.product_no_tracking.standard_price, 350)
        self.assertEqual(picking_in_01.move_lines.price_unit, 225)
        self.assertEqual(picking_in_01.move_lines.value, 900)
        self.assertEqual(
            sum(self.product_tracking_lot.stock_move_ids.mapped('value')),
            900)
        self.assertEqual(picking_in_02.move_lines.price_unit, 350)
        self.assertEqual(picking_in_02.move_lines.value, 700)
        self.assertEqual(
            sum(self.product_no_tracking.stock_move_ids.mapped('value')),
            700)
