###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.addons.mrp.tests.common import TestMrpCommon
from odoo.tests import Form


class TestMrpProductionFinishedProducts(TestMrpCommon):

    def create_wizard(self, mo):
        move_line = mo.move_finished_ids.move_line_ids.with_context(
            default_production_id=mo.id)[0]
        action = move_line.action_mrp_finished_product_details()
        detail_obj = self.env['mrp.production.finished_detail']
        return detail_obj.browse(action['res_id'])

    def test_production(self):
        quant_obj = self.env['stock.quant']
        product_obj = self.env['product.product']
        stock_location = self.env.ref('stock.stock_location_stock')
        product = product_obj.create({
            'name': 'Table',
            'type': 'product',
        })
        lot = self.env['stock.production.lot'].create({
            'product_id': product.id,
        })
        component1 = product_obj.create({
            'name': 'Table head',
            'type': 'product',
        })
        component2 = product_obj.create({
            'name': 'Table stand',
            'type': 'product',
        })
        bom = self.env['mrp.bom'].create({
            'product_id': product.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_uom_id': self.uom_unit.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {'product_id': component1.id, 'product_qty': 1}),
                (0, 0, {'product_id': component2.id, 'product_qty': 1})
            ]})
        quant_obj._update_available_quantity(component1, stock_location, 2)
        quant_obj._update_available_quantity(component2, stock_location, 2)
        mo = self.env['mrp.production'].create({
            'name': 'MO 1',
            'product_id': product.id,
            'product_uom_id': product.uom_id.id,
            'product_qty': 10.0,
            'bom_id': bom.id,
        })
        self.assertEqual(len(mo), 1)
        mo.action_assign()
        produce_form = Form(self.env['mrp.product.produce'].with_context({
            'active_id': mo.id,
            'active_ids': [mo.id],
        }))
        produce_form.product_qty = 10
        produce_wizard = produce_form.save()
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(len(mo.move_finished_ids.move_line_ids), 0)
        self.assertEqual(len(mo.finished_move_line_ids), 0)
        produce_wizard.do_produce()
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(len(mo.finished_move_line_ids), 1)
        wizard = self.create_wizard(mo)
        wizard.line_ids[0].qty_done = 9
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'qty_done': 1,
        })
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(sum(wizard.line_ids.mapped('qty_done')), 10)
        wizard.action_confirm()
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(len(mo.move_finished_ids.move_line_ids), 1)
        wizard = self.create_wizard(mo)
        wizard.line_ids.unlink()
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'qty_done': 3,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'qty_done': 3,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'qty_done': 3,
        })
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(sum(wizard.line_ids.mapped('qty_done')), 9)
        wizard.action_confirm()
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(len(mo.move_finished_ids.move_line_ids), 1)
        self.assertEqual(
            sum(mo.move_finished_ids.move_line_ids.mapped('qty_done')), 10)
        wizard = self.create_wizard(mo)
        wizard.line_ids.unlink()
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'qty_done': 100,
        })
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(sum(wizard.line_ids.mapped('qty_done')), 100)
        with self.assertRaises(exceptions.ValidationError):
            wizard.action_confirm()
        wizard = self.create_wizard(mo)
        wizard.line_ids.unlink()
        wizard.action_confirm()
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(len(mo.move_finished_ids.move_line_ids), 1)
        self.assertEqual(mo.move_finished_ids.move_line_ids.qty_done, 10)
        wizard = self.create_wizard(mo)
        wizard.line_ids.unlink()
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'lot_id': lot.id,
            'qty_done': 1,
        })
        package = self.env['stock.quant.package'].create({})
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'result_package_id': package.id,
            'qty_done': 1,
        })
        wizard.action_confirm()
        self.assertEqual(len(mo.move_finished_ids.move_line_ids), 3)
        self.assertEqual(
            sum(mo.move_finished_ids.move_line_ids.mapped('qty_done')), 10)
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')
        self.assertEqual(
            quant_obj._get_available_quantity(product, stock_location),
            10)
        self.assertEqual(
            quant_obj._get_available_quantity(component1, stock_location),
            0)
        self.assertEqual(
            quant_obj._get_available_quantity(component2, stock_location),
            0)
        self.assertEquals(len(mo.move_finished_ids), 1)
        packages = mo.finished_move_line_ids.mapped('result_package_id')
        self.assertEquals(len(packages), 1)
        self.assertEquals(packages.quant_ids.mapped('product_id'), product)
        self.assertEquals(
            sum(mo.finished_move_line_ids.mapped('qty_done')), 10)
