# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import tools, exceptions, _
import os
import logging
_log = logging.getLogger(__name__)


class TestPrintReport(common.TransactionCase):

    def setUp(self):
        super(TestPrintReport, self).setUp()
        self.product_obj = self.env['product.product']
        self.lot_obj = self.env['stock.production.lot']

        # Create products
        self.product_01 = self.product_obj.create({
            'name': 'Product 01',
            'ean13': '0075678164125',
            'default_code': 'COD-PROD-1'})
        self.lot_01 = self.lot_obj.create({
            'name': 'LOT-000001',
            'product_id': self.product_01.id})
        self.product_02 = self.product_obj.create({
            'name': 'Product 02',
            'ean13': '0000000350006',
            'default_code': 'COD-PROD-2'})
        self.lot_02 = self.lot_obj.create({
            'name': 'LOT-000002',
            'product_id': self.product_02.id})
        self.product_03 = self.product_obj.create({
            'name': 'Product 03',
            'default_code': 'COD-PROD-3'})
        self.lot_03 = self.lot_obj.create({
            'name': 'LOT-000003',
            'product_id': self.product_03.id})
        self.lot_04 = self.lot_obj.create({
            'name': 'LOT-000004',
            'product_id': self.product_03.id})

        self.picking_01 = self.env['stock.picking'].create({
            'company_id': self.env.user.company_id.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id})
        self.move_01 = self.env['stock.move'].create({
            'product_id': self.product_01.id,
            'product_uom_qty': 3,
            'product_uom': self.env.ref('product.product_uom_unit').id,
            'name': self.product_01.name,
            'location_dest_id': self.env.ref(
                'stock.stock_location_customers').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'picking_id': self.picking_01.id,
            'lot_ids': [(6, 0, [self.lot_01.id, self.lot_02.id])]})
        self.move_02 = self.env['stock.move'].create({
            'product_id': self.product_02.id,
            'product_uom_qty': 2,
            'product_uom': self.env.ref('product.product_uom_unit').id,
            'name': self.product_02.name,
            'location_dest_id': self.env.ref(
                'stock.stock_location_customers').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'picking_id': self.picking_01.id,
            'lot_ids': [(6, 0, [self.lot_03.id])]})

    def test_print_product_label_picking_one_report(self):
        '''Print product label from picking with 'quantity_picking' is 'one'.
        '''
        wiz = self.env['wiz.product.label'].with_context(
            dict(active_ids=[self.picking_01.id])).create({
                'quantity_picking': 'one'})
        re = wiz.button_print_from_picking()
        ctx = re['context']
        ctx.update(dict(active_ids=[self.picking_01.move_lines]))

        def print_report(fname):
            pdf = self.env['report'].with_context(ctx).get_pdf(
                self.picking_01.move_lines,
                re['report_name'], data=re['datas'])
            with open(fname, 'w') as fp:
                fp.write(pdf)

        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'product_label_picking_one.pdf')
        print_report(instance_path)

    def test_print_product_label_picking_line_report(self):
        '''Print product label from picking with 'quantity_picking' is 'line'.
        '''
        wiz = self.env['wiz.product.label'].with_context(
            dict(active_ids=[self.picking_01.id])).create({
                'quantity_picking': 'line'})
        re = wiz.button_print_from_picking()
        ctx = re['context']
        ctx.update(dict(active_ids=[self.picking_01.move_lines]))

        def print_report(fname):
            pdf = self.env['report'].with_context(ctx).get_pdf(
                self.picking_01.move_lines,
                re['report_name'], data=re['datas'])
            with open(fname, 'w') as fp:
                fp.write(pdf)

        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'product_label_picking_line.pdf')
        print_report(instance_path)

    def test_print_product_label_picking_total_error_report(self):
        '''Print product label from picking with 'quantity_picking' is 'total'.
        It will fail and display the raise message because the picking is not
        transferred.
        '''
        wiz = self.env['wiz.product.label'].with_context(
            dict(active_ids=[self.picking_01.id])).create({
                'quantity_picking': 'total'})
        try:
            wiz.button_print_from_picking()
            self.assertFail()
        except Exception as e:
            msg = ('No hay operaciones, para imprimir este tipo de etiqueta '
                   'debe transferir el albarán.')
            self.assertEqual(e.message, unicode(msg, 'utf-8'))

    def test_print_product_label_picking_total_report(self):
        '''Print product label from picking with 'quantity_picking' is 'total'.
        '''
        # Confirm and transfer picking
        self.picking_01.action_confirm()
        self.picking_01.action_assign()
        self.picking_01.do_prepare_partial()
        self.picking_01.do_transfer()
        # Get one of the operations that have been generated by transferring
        # the picking
        if not self.picking_01.pack_operation_ids.exists:
            raise exceptions.Warning(_(
                'Does not exist pack_operation_ids for this picking.'))
        wiz = self.env['wiz.product.label'].with_context(
            dict(active_ids=[self.picking_01.id])).create({
                'quantity_picking': 'total'})
        re = wiz.button_print_from_picking()
        ctx = re['context']

        def print_report(fname):
            pdf = self.env['report'].with_context(ctx).get_pdf(
                self.picking_01.pack_operation_ids,
                re['report_name'], data=re['datas'])
            with open(fname, 'w') as fp:
                fp.write(pdf)

        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'product_label_picking_total.pdf')
        print_report(instance_path)
