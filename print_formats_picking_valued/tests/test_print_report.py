# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields, tools, exceptions, _
import os
import logging
_log = logging.getLogger(__name__)


class TestPrintReport(common.TransactionCase):
    def setUp(self):
        super(TestPrintReport, self).setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})

        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'default_code': '123456'})

        self.pt_02 = self.env['product.template'].create({
            'name': 'Product 02',
            'type': 'product'})

        self.pp_02 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_02.id,
            'default_code': '123456',
            'uom_id': self.ref('product.product_uom_unit')})

        wh = self.env['stock.warehouse'].search([
            ('company_id', '=', self.ref('base.main_company'))])
        if not wh.exists():
            raise exceptions.Warning(_(
                'Does not exist any warehouse for main company.'))

        self.picking_01 = self.env['stock.picking'].create({
            'partner_id': self.partner_01.id,
            'date_done': fields.Date.today(),
            'move_type': 'direct',
            'company_id': self.ref('base.main_company'),
            'picking_type_id': wh[0].out_type_id.id,
            'state': 'done',
            'min_date': fields.Date.today(),
            'max_date': fields.Date.today(),
            'date': fields.Date.today(),
            'invoice_state': 'none'})

        self.move_01 = self.env['stock.move'].create({
            'picking_id': self.picking_01.id,
            'product_id': self.pp_01.id,
            'name': self.pp_01.name_template,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
            'picking_type_id': wh[0].out_type_id.id,
            'location_id': self.ref('stock.stock_location_stock'),
            'location_dest_id': self.ref('stock.stock_location_customers')})
        self.move_02 = self.env['stock.move'].create({
            'picking_id': self.picking_01.id,
            'product_id': self.pp_02.id,
            'name': self.pp_02.name_template,
            'product_uom_qty': 3,
            'product_uom': self.ref('product.product_uom_unit'),
            'picking_type_id': wh[0].out_type_id.id,
            'location_id': self.ref('stock.stock_location_stock'),
            'location_dest_id': self.ref('stock.stock_location_customers')})

        pricelist = self.env['product.pricelist'].create({
            'name': '10% discount',
            'type': 'sale'})
        version = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist.id,
            'name': '10% discount version'})
        self.env['product.pricelist.item'].create({
            'price_version_id': version.id,
            'name': '10% discount item',
            'sequence': 10,
            'base': self.ref('product.list_price'),
            'price_discount': -0.1})

        self.order_01 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': pricelist.id,
            'date_order': fields.Date.today(),
            'note': 'Comment...',
            'payment_term': self.payment_term.id,
            'company_id': self.company.id,
            'section_id': self.ref('sales_team.section_sales_department'),
            'client_order_ref': '016/81601863/ BM PALMA DE MALLORCA'})

        self.order_line_description = self.env['sale.order.line'].create({
            'order_id': self.order_01.id,
            'name': 'Description 1',
            'product_uom_qty': 1,
            'price_unit': 33.25,
            'product_uom': self.ref('product.product_uom_unit'),
            'company_id': self.company.id,
            'tax_id': [(6, 0, [self.taxs_21.id])]})

        self.order_line_01 = self.env['sale.order.line'].create({
            'order_id': self.order_01.id,
            'product_id': self.pp_01.id,
            'product_uom_qty': 2,
            'product_uom': self.ref('product.product_uom_unit')})

        # Check if pricelist applies in price lines
        self.assertEqual(self.order_line_01.price_unit, 0.9)
        # Confirm sale order
        self.order_01.signal_workflow('order_confirm')
        # Check that picking has been created.
        self.assertEqual(len(self.order_01.picking_ids), 1)
        # Confirm picking and transfer
        self.picking_02 = self.order_01.picking_ids[0]

    def print_report(self, obj, rname, fname):
        pdf = self.env['report'].get_pdf(obj, rname)
        with open(fname, 'w') as fp:
            fp.write(pdf)

    def test_print_picking_without_sale_report(self):
        '''Return product prices.'''
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'test_report_picking_valued_without_sale.pdf')
        self.print_report(
            self.picking_01,
            'print_formats_picking_valued.report_picking_valued',
            instance_path)

    def test_print_picking_with_sale_report(self):
        '''Return product prices applying pricelist.'''
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'test_report_picking_valued_with_sale.pdf')
        self.print_report(
            self.picking_02,
            'print_formats_picking_valued.report_picking_valued',
            instance_path)
