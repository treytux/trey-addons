###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.addons.mrp.tests.common import TestMrpCommon
from odoo.tests import Form


class TestMrpPackageDummy(TestMrpCommon):

    def test_production(self):
        quant_obj = self.env['stock.quant']
        product_obj = self.env['product.product']
        stock_location = self.env.ref('stock.stock_location_stock')
        product = product_obj.create({
            'name': 'Table',
            'type': 'product',
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
            'product_qty': 2.0,
            'bom_id': bom.id,
        })
        self.assertEqual(len(mo), 1)
        mo.action_assign()
        produce_form = Form(self.env['mrp.product.produce'].with_context({
            'active_id': mo.id,
            'active_ids': [mo.id],
        }))
        produce_form.product_qty = 2.0
        produce_wizard = produce_form.save()
        produce_wizard.do_produce()
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'product_id': mo.product_id.id,
        })
        wizard.action_print()
        barcodes = wizard.get_barcodes()
        action = mo.action_package_dummy_read()
        wizard_create = self.env[action['res_model']].browse(action['res_id'])
        wizard_create.barcodes = '\n'.join(barcodes)
        wizard_create.action_run()
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')
        self.assertEqual(
            quant_obj._get_available_quantity(product, stock_location),
            2)
        self.assertEqual(
            quant_obj._get_available_quantity(component1, stock_location),
            0)
        self.assertEqual(
            quant_obj._get_available_quantity(component2, stock_location),
            0)
        self.assertEquals(len(mo.finished_move_line_ids), 2)
        packages = mo.finished_move_line_ids.mapped('result_package_id')
        self.assertEquals(len(packages), len(barcodes))
        self.assertEquals(sum(mo.finished_move_line_ids.mapped('qty_done')), 2)

    def test_production_repeat_barcodes(self):
        quant_obj = self.env['stock.quant']
        product_obj = self.env['product.product']
        stock_location = self.env.ref('stock.stock_location_stock')
        product = product_obj.create({
            'name': 'Table',
            'type': 'product',
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
        quant_obj._update_available_quantity(component1, stock_location, 10)
        quant_obj._update_available_quantity(component2, stock_location, 10)
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
        produce_form.product_qty = 10.0
        produce_wizard = produce_form.save()
        produce_wizard.do_produce()
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'product_id': mo.product_id.id,
        })
        wizard.action_print()
        barcodes = wizard.get_barcodes()
        action = mo.action_package_dummy_read()
        wizard_create = self.env[action['res_model']].browse(action['res_id'])
        wizard_create.barcodes = '\n'.join(barcodes)
        wizard_create.action_run()
        self.assertEquals(len(mo.finished_move_line_ids), 3)
        packages = mo.finished_move_line_ids.mapped('result_package_id')
        self.assertEquals(len(packages), len(barcodes))
        self.assertEquals(
            sum(mo.finished_move_line_ids.mapped('qty_done')), 10)
        action = mo.action_package_dummy_read()
        wizard_create = self.env[action['res_model']].browse(action['res_id'])
        wizard_create.barcodes = '\n'.join(barcodes)
        wizard_create.action_simulate()
        self.assertEquals(len(wizard_create.line_ids), 2)

    def test_production_with_lot_and_packaging(self):
        quant_obj = self.env['stock.quant']
        product_obj = self.env['product.product']
        stock_location = self.env.ref('stock.stock_location_stock')
        product = product_obj.create({
            'name': 'Table',
            'type': 'product',
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
        product.packaging_ids = [(0, 0, {
            'name': 'Box 6',
            'qty': 6,
            'barcode': '1234567890123',
        })]
        lot = self.env['stock.production.lot'].create({
            'product_id': product.id,
        })
        quant_obj._update_available_quantity(component1, stock_location, 12)
        quant_obj._update_available_quantity(component2, stock_location, 12)
        mo = self.env['mrp.production'].create({
            'name': 'MO 1',
            'product_id': product.id,
            'product_uom_id': product.uom_id.id,
            'product_qty': 12.0,
            'bom_id': bom.id,
        })
        self.assertEqual(len(mo), 1)
        mo.action_assign()
        produce_form = Form(self.env['mrp.product.produce'].with_context({
            'active_id': mo.id,
            'active_ids': [mo.id],
        }))
        produce_form.product_qty = 12
        produce_wizard = produce_form.save()
        produce_wizard.do_produce()
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'product_id': mo.product_id.id,
            'packaging_id': product.packaging_ids[0].id,
            'lot_id': lot.id,
        })
        wizard.action_print()
        barcodes = wizard.get_barcodes()
        action = mo.action_package_dummy_read()
        wizard_create = self.env[action['res_model']].browse(action['res_id'])
        wizard_create.barcodes = '\n'.join(barcodes)
        wizard_create.action_simulate()
        self.assertEquals(len(wizard_create.line_ids), 0)
        wizard_create.action_run()
        action = mo.action_package_dummy_read()
        wizard_create = self.env[action['res_model']].browse(action['res_id'])
        wizard_create.barcodes = '\n'.join(barcodes)
        wizard_create.action_simulate()
        self.assertEquals(len(wizard_create.line_ids), 2)
        with self.assertRaises(exceptions.UserError):
            wizard_create.action_run()
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')
        self.assertEqual(
            quant_obj._get_available_quantity(product, stock_location),
            12)
        self.assertEqual(
            quant_obj._get_available_quantity(component1, stock_location),
            0)
        self.assertEqual(
            quant_obj._get_available_quantity(component2, stock_location),
            0)
        self.assertEquals(len(mo.finished_move_line_ids), 2)
        packages = mo.finished_move_line_ids.mapped('result_package_id')
        self.assertEquals(len(packages), len(barcodes))
        self.assertEquals(
            sum(mo.finished_move_line_ids.mapped('qty_done')), 12)
