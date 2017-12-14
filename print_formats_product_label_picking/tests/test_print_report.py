# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import tools, fields
import os
import logging
_log = logging.getLogger(__name__)


class TestPrintReport(common.TransactionCase):

    def setUp(self):
        super(TestPrintReport, self).setUp()
        # self.company = self.env['res.company'].create({
        #     'name': 'test'})

        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})

        self.product_01 = self.env['product.product'].create({
            'name': 'Product 01',
            'ean13': '0075678164125',
            'default_code': 'COD-PROD-1'})
        self.lot_01 = self.env['stock.production.lot'].create({
            'name': 'LOT-000001',
            'product_id': self.product_01.id})

        self.product_02 = self.env['product.product'].create({
            'name': 'Product 02',
            'ean13': '0000000350006',
            'default_code': 'COD-PROD-2'})
        self.lot_02 = self.env['stock.production.lot'].create({
            'name': 'LOT-000002',
            'product_id': self.product_02.id})

        self.product_03 = self.env['product.product'].create({
            'name': 'Product 03',
            'default_code': 'COD-PROD-3'})
        self.lot_03 = self.env['stock.production.lot'].create({
            'name': 'LOT-000003',
            'product_id': self.product_03.id})
        self.lot_04 = self.env['stock.production.lot'].create({
            'name': 'LOT-000004',
            'product_id': self.product_03.id})

        secuence = self.env['ir.sequence'].create({
            'name': 'Your Company Sequence in',
            'prefix': 'W1',
            'active': True,
            'padding': 5,
            'number_next_actual': 2,
            'number_increment': 1,
            'implementation': 'standard'})

        self.stock_location = self.env['stock.location'].create({
            'name': 'existencias',
            'usage': 'internal',
            'active': True})

        self.location = self.env['stock.location'].create({
            'name': 'existences source',
            'usage': 'internal',
            'active': True})

        self.stock_picking_type = self.env['stock.picking.type'].create({
            'name': 'Recepciones',
            'sequence_id': secuence.id,
            'code': 'incoming',
            'default_location_dest_id': self.stock_location.id})
        self.stock_picking = self.env['stock.picking'].create({
            'partner_id': self.partner_01.id,
            'date': fields.Date.today(),
            'origin': 'POE12',
            'note': 'Comment...',
            'state': 'confirmed',
            'move_type': 'direct',
            'invoice_state': '2binvoiced',
            'picking_type_id': self.ref('stock.picking_type_in'),
            'weight_uom_id': self.ref('product.product_uom_unit'),
            'priority': '1',
            'company_id': self.ref('base.main_company')})

        self.move_01 = self.env['stock.move'].create({
            'picking_id': self.stock_picking.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 3,
            'name': self.product_01.name,
            'date': fields.Date.today(),
            'date_expected': fields.Date.today(),
            'price_unit': 33.25,
            'product_uom': self.env.ref('product.product_uom_unit').id,
            'location_dest_id': self.stock_location.id,
            'location_id': self.location.id,
            'lot_ids': [(6, 0, [self.lot_01.id, self.lot_02.id])],
            'company_id': self.ref('base.main_company')})

        self.move_02 = self.env['stock.move'].create({
            'picking_id': self.stock_picking.id,
            'product_id': self.product_02.id,
            'product_uom_qty': 3,
            'name': self.product_02.name,
            'date': fields.Date.today(),
            'date_expected': fields.Date.today(),
            'price_unit': 33.25,
            'product_uom': self.env.ref('product.product_uom_unit').id,
            'location_dest_id': self.stock_location.id,
            'location_id': self.location.id,
            'lot_ids': [(6, 0, [self.lot_03.id])],
            'company_id': self.ref('base.main_company')})

    def test_print_product_label_picking_one_report(self):
        '''Print product label from picking with 'picking_quantity' is 'one'
        '''
        wiz = self.env['wiz.product.label'].with_context(
            dict(active_ids=[self.stock_picking.id])).create({
                'picking_quantity': 'one'})
        re = wiz.button_print_from_picking()
        ctx = re['context']
        ctx.update(dict(active_ids=[self.stock_picking.move_lines]))

        def print_report(fname):
            pdf = self.env['report'].with_context(ctx).get_pdf(
                self.stock_picking.move_lines,
                re['report_name'], data=re['datas'])
            with open(fname, 'w') as fp:
                fp.write(pdf)

        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'test_product_label_picking_one.pdf')
        print_report(instance_path)

    def test_print_product_label_picking_line_report(self):
        '''Print product label from picking with 'picking_quantity' is 'line'.
        '''
        wiz = self.env['wiz.product.label'].with_context(
            dict(active_ids=[self.stock_picking.id])).create({
                'picking_quantity': 'line'})
        re = wiz.button_print_from_picking()
        ctx = re['context']
        ctx.update(dict(active_ids=[self.stock_picking.move_lines]))

        def print_report(fname):
            pdf = self.env['report'].with_context(ctx).get_pdf(
                self.stock_picking.move_lines,
                re['report_name'], data=re['datas'])
            with open(fname, 'w') as fp:
                fp.write(pdf)

        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'test_product_label_picking_line.pdf')
        print_report(instance_path)
