# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import tools
import os
import logging
_log = logging.getLogger(__name__)


class TestPrintReport(common.TransactionCase):

    def setUp(self):
        super(TestPrintReport, self).setUp()
        self.product_obj = self.env['product.product']
        self.mrp_bom_obj = self.env['mrp.bom']
        self.production_obj = self.env['mrp.production']
        self.produce_obj = self.env['mrp.product.produce']
        self.produce_line_obj = self.env['mrp.product.produce.line']
        self.lot_obj = self.env['stock.production.lot']
        self.produce_wizard_obj = self.env['mrp.product.produce']
        product_vals = {
            'name': 'Produce product',
            'standard_price': 10.0,
            'list_price': 20.0,
            'type': 'product',
            'route_ids': [
                (6, 0,
                 [self.env.ref('mrp.route_warehouse0_manufacture').id,
                  self.env.ref('stock.route_warehouse0_mto').id])]}
        self.produce_product = self.product_obj.create(product_vals)
        product_vals = {
            'name': 'Consume product',
            'standard_price': 8.0,
            'list_price': 10.0,
            'type': 'product'}
        self.consume_product = self.product_obj.create(product_vals)
        self.lot_01 = self.lot_obj.create({
            'name': 'LOT-000001',
            'product_id': self.consume_product.id})
        bom_vals = {
            'product_tmpl_id': self.produce_product.product_tmpl_id.id,
            'product_id': self.produce_product.id,
            'bom_line_ids': [(0, 0, {'product_id': self.consume_product.id})]}
        self.bom = self.mrp_bom_obj.create(bom_vals)
        production_vals = {
            'product_id': self.produce_product.id,
            'bom_id': self.bom.id,
            'product_qty': 1,
            'product_uom': self.produce_product.uom_id.id}
        self.production_01 = self.production_obj.create(production_vals)
        production_vals = {
            'product_id': self.produce_product.id,
            'bom_id': self.bom.id,
            'product_qty': 2,
            'product_uom': self.produce_product.uom_id.id}
        self.production_02 = self.production_obj.create(production_vals)

    def print_report(self, obj, rname, fname):
        pdf = self.env['report'].get_pdf(obj, rname)
        with open(fname, 'w') as fp:
            fp.write(pdf)

    def test_print_mrp_order_report_01(self):
        '''Confirm mrp production 01.'''
        # Confirm mrp production
        self.production_01.action_confirm()
        # Check move_lines
        self.assertEqual(len(self.production_01.move_lines), 1)
        # Assign lot to move lines
        for m in self.production_01.move_lines:
            m.lot_ids = [(6, 0, [self.lot_01.id])]
        # Print report
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'report_mrporder_extend_01.pdf')
        self.print_report(
            self.production_01, 'mrp.report_mrporder',
            instance_path)

    def test_print_mrp_order_report_02(self):
        '''Confirm mrp production 02 and produce.'''
        # Confirm mrp production
        self.production_02.action_confirm()
        # Check move_lines
        self.assertEqual(len(self.production_02.move_lines), 1)
        # Assign lot to move lines
        for m in self.production_02.move_lines:
            m.lot_ids = [(6, 0, [self.lot_01.id])]
        # Print report
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'report_mrporder_extend_02.pdf')
        self.print_report(
            self.production_02, 'mrp.report_mrporder',
            instance_path)
        # Produce call wizard
        wizard = self.produce_wizard_obj.with_context({
            'active_ids': [self.production_02.id],
            'active_model': 'mrp.production',
            'active_id': self.production_02.id}).create({})
        # Produce
        wizard.do_produce()
        # Check move_lines2
        self.assertEqual(len(self.production_02.move_lines2), 1)
