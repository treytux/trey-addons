###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class PurchaseCostDistributionTest(TransactionCase):

    def setUp(self):
        super().setUp()
        if not self.env.company.chart_template_id:
            coa = self.env.ref('l10n_generic_coa.configurable_chart_template',
                               False)
            if not coa:
                coa = self.env['account.chart.template'].search([
                    ('visible', '=', True),
                ], limit=1)
            coa.try_loading(company=self.env.company, install_demo=False)
        expense_type_obj = self.env['purchase.expense.type']
        self.type_amount = expense_type_obj.create({
            'name': 'Type Amount',
            'calculation_method': 'amount',
            'default_amount': True,
        })
        self.type_price = expense_type_obj.create({
            'name': 'Type Price',
            'calculation_method': 'price',
        })
        self.type_qty = expense_type_obj.create({
            'name': 'Type Qty',
            'calculation_method': 'qty',
        })
        self.type_weight = expense_type_obj.create({
            'name': 'Type Weight',
            'calculation_method': 'weight',
        })
        self.type_volume = expense_type_obj.create({
            'name': 'Type Volume',
            'calculation_method': 'volume',
        })
        self.type_equal = expense_type_obj.create({
            'name': 'Type Equal',
            'calculation_method': 'equal',
        })
        self.distribution = self.env['purchase.cost.distribution'].create({
            'name': '/',
        })
        self.product_category_average = self.env['product.category'].create({
            'name': 'Landed Cost',
            'property_valuation': 'manual_periodic',
            'property_cost_method': 'average',
        })
        self.product_category_standard = self.env['product.category'].create({
            'name': 'Landed Cost',
            'property_valuation': 'manual_periodic',
            'property_cost_method': 'standard',
        })
        self.product_category_fifo = self.env['product.category'].create({
            'name': 'Landed Cost',
            'property_valuation': 'manual_periodic',
            'property_cost_method': 'fifo',
        })
        self.product_average = self.env['product.product'].create({
            'name': 'Product',
            'type': 'product',
            'categ_id': self.product_category_average.id,
        })
        self.product_standard = self.env['product.product'].create({
            'name': 'Product Standard',
            'type': 'product',
            'categ_id': self.product_category_standard.id,
            'standard_price': 3.0,
        })
        self.product_fifo = self.env['product.product'].create({
            'name': 'Product FIFO',
            'type': 'product',
            'categ_id': self.product_category_fifo.id,
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier',
        })
        account = self.env['account.account'].create({
            'name': 'Account',
            'code': 'CODE',
            'account_type': 'expense',
        })
        self.invoice = self.env['account.move'].create({
            'partner_id': self.supplier.id,
            'move_type': 'in_invoice',
            'invoice_date': datetime.now(),
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Test service',
                    'account_id': account.id,
                    'price_unit': 10.0,
                })
            ],
        })
        self.invoice._post()
        wiz = (self.env['import.invoice.line.wizard']
               .with_context(active_id=self.distribution.id).create({
                   'supplier': self.supplier.id,
                   'invoice': self.invoice.id,
                   'invoice_line': self.invoice.invoice_line_ids[:1].id,
                   'expense_type': self.type_qty.id,
               }))
        wiz.action_import_invoice_line()

    def create_purchase(self, product, price_unit, product_qty):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.supplier.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'product_qty': product_qty,
                    'name': product.name,
                    'product_uom': product.uom_id.id,
                    'price_unit': price_unit,
                    'date_planned': fields.Date.today(),
                })
            ],
        })
        purchase_order.button_confirm()
        picking = purchase_order.picking_ids
        self.env['stock.immediate.transfer'].create(
            {'pick_ids': [(4, picking.id)]}).process()
        picking.action_confirm()
        picking.move_ids.write({'quantity_done': product_qty})
        picking.button_validate()
        return picking

    def create_sale(self, product, product_qty):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.supplier.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': product_qty,
                    'name': product.name,
                    'product_uom': product.uom_id.id,
                    'price_unit': product.standard_price,
                })
            ],
        })
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        self.env['stock.immediate.transfer'].create(
            {'pick_ids': [(4, picking.id)]}).process()
        picking.action_confirm()
        picking.move_ids.write({'quantity_done': product_qty})
        picking.button_validate()
        return picking

    def test_distribution_without_lines(self):
        self.assertNotEqual(self.distribution.name, '/')
        with self.assertRaises(UserError):
            self.distribution.action_calculate()
        self.assertEqual(self.distribution.state, 'draft')

    def test_done_to_draft_flow_with_cost_method_average(self):
        picking_average = self.create_purchase(self.product_average, 3.0, 5.0)
        self.assertEqual(picking_average.state, 'done')
        wiz = (self.env['picking.import.wizard']
               .with_context(active_id=self.distribution.id).create({
                   'supplier': self.supplier.id,
                   'pickings': [(6, 0, picking_average.ids)],
               }))
        wiz.action_import_picking()
        action = picking_average.action_view_stock_valuation_layers()
        valuation_layer = self.env['stock.valuation.layer']
        valuation_layer = valuation_layer.browse(action['domain'][0][2][0])
        self.assertEqual(len(self.distribution.cost_lines.ids), 1)
        self.assertAlmostEqual(self.distribution.total_uom_qty, 5.0)
        self.assertAlmostEqual(self.distribution.total_purchase, 15.0)
        self.assertAlmostEqual(self.distribution.amount_total, 25.0)
        self.assertEqual(len(self.distribution.expense_lines.ids), 1)
        self.assertAlmostEqual(self.distribution.total_uom_qty, 5.0)
        self.distribution.action_calculate()
        self.assertAlmostEqual(self.distribution.cost_lines[0].cost_ratio, 2)
        self.assertAlmostEqual(self.distribution.total_expense, 10.0)
        self.assertEqual(self.distribution.state, 'calculated')
        self.distribution.action_done()
        self.assertEqual(self.distribution.state, 'done')
        self.assertEqual(self.product_average.standard_price, 5)
        self.assertEqual(valuation_layer.product_id.id, self.product_average.id)
        self.assertEqual(valuation_layer.quantity, 5)
        self.assertEqual(valuation_layer.unit_cost, 5)
        self.assertEqual(valuation_layer.value, 25)
        with self.assertRaises(UserError) as context:
            self.distribution.action_draft()
        self.assertIn('Cost update cannot be undone', str(context.exception))
        self.distribution.expense_lines.unlink()
        self.distribution.action_draft()
        self.assertEqual(self.product_average.standard_price, 3)
        self.assertAlmostEqual(self.distribution.amount_total, 15.0)
        self.assertEqual(len(self.distribution.expense_lines.ids), 0)

    def test_done_to_draft_flow_with_cost_method_standard(self):
        picking_standard = self.create_purchase(
            self.product_standard, 3.0, 5.0)
        self.assertEqual(picking_standard.state, 'done')
        wiz = (self.env['picking.import.wizard']
               .with_context(active_id=self.distribution.id).create({
                   'supplier': self.supplier.id,
                   'pickings': [(6, 0, picking_standard.ids)],
               }))
        wiz.action_import_picking()
        action = picking_standard.action_view_stock_valuation_layers()
        valuation_layer = self.env['stock.valuation.layer']
        valuation_layer = valuation_layer.browse(action['domain'][0][2][0])
        self.assertEqual(len(self.distribution.cost_lines.ids), 1)
        self.assertAlmostEqual(self.distribution.total_uom_qty, 5.0)
        self.assertAlmostEqual(self.distribution.total_purchase, 15.0)
        self.assertAlmostEqual(self.distribution.amount_total, 25.0)
        self.assertEqual(len(self.distribution.expense_lines.ids), 1)
        self.assertAlmostEqual(self.distribution.total_uom_qty, 5.0)
        self.distribution.action_calculate()
        self.assertAlmostEqual(self.distribution.cost_lines[0].cost_ratio, 2)
        self.assertAlmostEqual(self.distribution.total_expense, 10.0)
        self.assertEqual(self.distribution.state, 'calculated')
        self.distribution.action_done()
        self.assertEqual(self.distribution.state, 'done')
        self.assertEqual(self.product_standard.standard_price, 3)
        self.assertEqual(valuation_layer.product_id.id,
                         self.product_standard.id)
        self.assertEqual(valuation_layer.quantity, 5)
        self.assertEqual(valuation_layer.unit_cost, 5)
        self.assertEqual(valuation_layer.value, 25)
        self.distribution.expense_lines.unlink()
        self.distribution.action_draft()
        self.assertEqual(self.product_standard.standard_price, 3)
        self.assertAlmostEqual(self.distribution.amount_total, 15.0)
        self.assertEqual(len(self.distribution.expense_lines.ids), 0)
        self.assertEqual(valuation_layer.quantity, 5)
        self.assertEqual(valuation_layer.unit_cost, 3)
        self.assertEqual(valuation_layer.value, 15)

    def test_done_to_draft_flow_with_cost_method_fifo_change_standard_price(
            self):
        picking_fifo = self.create_purchase(self.product_fifo, 3.0, 5.0)
        self.assertEqual(picking_fifo.state, 'done')
        wiz = (self.env['picking.import.wizard']
               .with_context(active_id=self.distribution.id).create({
                   'supplier': self.supplier.id,
                   'pickings': [(6, 0, picking_fifo.ids)],
               }))
        wiz.action_import_picking()
        action = picking_fifo.action_view_stock_valuation_layers()
        valuation_layer = self.env['stock.valuation.layer']
        valuation_layer = valuation_layer.browse(action['domain'][0][2][0])
        self.assertEqual(len(self.distribution.cost_lines.ids), 1)
        self.assertAlmostEqual(self.distribution.total_uom_qty, 5.0)
        self.assertAlmostEqual(self.distribution.total_purchase, 15.0)
        self.assertAlmostEqual(self.distribution.amount_total, 25.0)
        self.assertEqual(len(self.distribution.expense_lines.ids), 1)
        self.assertAlmostEqual(self.distribution.total_uom_qty, 5.0)
        self.distribution.action_calculate()
        self.assertAlmostEqual(self.distribution.cost_lines[0].cost_ratio, 2)
        self.assertAlmostEqual(self.distribution.total_expense, 10.0)
        self.assertEqual(self.distribution.state, 'calculated')
        self.assertEqual(valuation_layer.quantity, 5)
        self.assertEqual(valuation_layer.unit_cost, 3)
        self.assertEqual(valuation_layer.value, 15)
        self.assertEqual(valuation_layer.remaining_qty, 5)
        self.assertEqual(valuation_layer.remaining_value, 15)
        self.distribution.action_done()
        self.assertEqual(self.distribution.state, 'done')
        self.assertEqual(self.product_fifo.standard_price, 5)
        self.assertEqual(valuation_layer.product_id.id, self.product_fifo.id)
        self.assertEqual(valuation_layer.quantity, 5)
        self.assertEqual(valuation_layer.unit_cost, 5)
        self.assertEqual(valuation_layer.value, 25)
        self.assertEqual(valuation_layer.remaining_qty, 5)
        self.assertEqual(valuation_layer.remaining_value, 25)
        self.distribution.expense_lines.unlink()
        self.distribution.action_draft()
        self.assertEqual(self.product_fifo.standard_price, 3)
        self.assertAlmostEqual(self.distribution.amount_total, 15.0)
        self.assertEqual(len(self.distribution.expense_lines.ids), 0)
        self.assertEqual(valuation_layer.quantity, 5)
        self.assertEqual(valuation_layer.unit_cost, 3)
        self.assertEqual(valuation_layer.value, 15)
        self.assertEqual(valuation_layer.remaining_qty, 5)
        self.assertEqual(valuation_layer.remaining_value, 15)

    def test_done_to_draft_flow_with_cost_method_fifo_no_change_standard_price(
            self):
        picking_fifo = self.create_purchase(self.product_fifo, 3.0, 5.0)
        self.assertEqual(picking_fifo.state, 'done')
        picking_fifo2 = self.create_purchase(self.product_fifo, 90.0, 10.0)
        self.assertEqual(picking_fifo2.state, 'done')
        wiz = (self.env['picking.import.wizard']
               .with_context(active_id=self.distribution.id).create({
                   'supplier': self.supplier.id,
                   'pickings': [(6, 0, picking_fifo2.ids)],
               }))
        wiz.action_import_picking()
        action = picking_fifo2.action_view_stock_valuation_layers()
        valuation_layer = self.env['stock.valuation.layer']
        valuation_layer = valuation_layer.browse(action['domain'][0][2][0])
        self.assertEqual(len(self.distribution.cost_lines.ids), 1)
        self.assertAlmostEqual(self.distribution.total_uom_qty, 10.0)
        self.assertAlmostEqual(self.distribution.total_purchase, 900.0)
        self.assertAlmostEqual(self.distribution.amount_total, 910.0)
        self.assertEqual(len(self.distribution.expense_lines.ids), 1)
        self.assertAlmostEqual(self.distribution.total_uom_qty, 10.0)
        self.distribution.action_calculate()
        self.assertAlmostEqual(self.distribution.cost_lines[0].cost_ratio, 1)
        self.assertAlmostEqual(self.distribution.total_expense, 10)
        self.assertEqual(self.distribution.state, 'calculated')
        self.distribution.action_done()
        self.assertEqual(self.distribution.state, 'done')
        self.assertEqual(self.product_fifo.standard_price, 3)

        self.assertEqual(valuation_layer.product_id.id, self.product_fifo.id)
        self.assertEqual(valuation_layer.quantity, 10)
        self.assertEqual(valuation_layer.unit_cost, 91)
        self.assertEqual(valuation_layer.value, 910)
        self.distribution.expense_lines.unlink()
        self.distribution.action_draft()
        self.assertEqual(self.product_fifo.standard_price, 3)
        self.assertAlmostEqual(self.distribution.amount_total, 900)
        self.assertEqual(len(self.distribution.expense_lines.ids), 0)
        self.assertEqual(valuation_layer.quantity, 10)
        self.assertEqual(valuation_layer.unit_cost, 90)
        self.assertEqual(valuation_layer.value, 900)

    def test_fifo_sale_with_new_standard_price_and_reverted_distribution(self):
        picking_fifo = self.create_purchase(self.product_fifo, 3.0, 5.0)
        self.assertEqual(picking_fifo.state, 'done')
        wiz = (self.env['picking.import.wizard']
               .with_context(active_id=self.distribution.id).create({
                   'supplier': self.supplier.id,
                   'pickings': [(6, 0, picking_fifo.ids)],
               }))
        wiz.action_import_picking()
        action = picking_fifo.action_view_stock_valuation_layers()
        valuation_layer = self.env['stock.valuation.layer']
        valuation_layer = valuation_layer.browse(action['domain'][0][2][0])
        self.assertEqual(len(self.distribution.cost_lines.ids), 1)
        self.assertAlmostEqual(self.distribution.total_uom_qty, 5.0)
        self.assertAlmostEqual(self.distribution.total_purchase, 15.0)
        self.assertAlmostEqual(self.distribution.amount_total, 25.0)
        self.assertEqual(len(self.distribution.expense_lines.ids), 1)
        self.assertAlmostEqual(self.distribution.total_uom_qty, 5.0)
        self.distribution.action_calculate()
        self.assertAlmostEqual(self.distribution.cost_lines[0].cost_ratio, 2)
        self.assertAlmostEqual(self.distribution.total_expense, 10.0)
        self.assertEqual(self.distribution.state, 'calculated')
        self.assertEqual(valuation_layer.quantity, 5)
        self.assertEqual(valuation_layer.unit_cost, 3)
        self.assertEqual(valuation_layer.value, 15)
        self.assertEqual(valuation_layer.remaining_qty, 5)
        self.assertEqual(valuation_layer.remaining_value, 15)
        self.distribution.action_done()
        self.assertEqual(self.distribution.state, 'done')
        self.assertEqual(self.product_fifo.standard_price, 5)
        self.assertEqual(valuation_layer.product_id.id, self.product_fifo.id)
        self.assertEqual(valuation_layer.quantity, 5)
        self.assertEqual(valuation_layer.unit_cost, 5)
        self.assertEqual(valuation_layer.value, 25)
        self.assertEqual(valuation_layer.remaining_qty, 5)
        self.assertEqual(valuation_layer.remaining_value, 25)
        picking_fifo2 = self.create_purchase(self.product_fifo, 90.0, 10.0)
        self.assertEqual(picking_fifo2.state, 'done')
        sale_picking_fifo = self.create_sale(self.product_fifo, 5.0)
        self.assertEqual(sale_picking_fifo.sale_id.order_line.price_unit, 5)
        self.assertEqual(self.product_fifo.standard_price, 90)
        self.distribution.expense_lines.unlink()
        self.distribution.action_draft()
        self.assertEqual(self.product_fifo.standard_price, 90)
