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
        self.partner_obj = self.env['res.partner']
        self.product_obj = self.env['product.product']
        self.order_obj = self.env['sale.order']
        self.order_line_obj = self.env['sale.order.line']

        # Create partner
        partner_data = {
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'}
        self.partner_01 = self.partner_obj.create(partner_data)

        # Create products
        self.product_01 = self.product_obj.create({
            'name': 'Product 01',
            'ean13': '0075678164125',
            'default_code': 'COD-PROD-1'})

        # Create sale order
        order_01_data = {
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'section_id': self.ref('sales_team.section_sales_department'),
            'date_order': fields.Date.today()}
        self.order_01 = self.order_obj.create(order_01_data)

        # Create sale order lines
        order_line_01_data = {
            'order_id': self.order_01.id,
            'name': 'Description 1',
            'product_uom_qty': 3,
            'price_unit': 33.25,
            'product_uom': self.ref('product.product_uom_unit')}
        self.order_line_01 = self.order_line_obj.create(order_line_01_data)
        order_line_02_data = {
            'order_id': self.order_01.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit')}
        self.order_line_02 = self.order_line_obj.create(order_line_02_data)

    def test_print_product_label_sale_line_report(self):
        '''Print product label from sale with 'quantity' is 'line'.'''
        wiz = self.env['wiz.product.label'].with_context(
            dict(active_ids=[self.order_01.id])).create({
                'quantity': 'line'})
        re = wiz.button_print_from_sale()
        ctx = re['context']
        ctx.update(dict(active_ids=[self.order_01.order_line]))

        def print_report(fname):
            pdf = self.env['report'].with_context(ctx).get_pdf(
                self.order_01.order_line,
                re['report_name'], data=re['datas'])
            with open(fname, 'w') as fp:
                fp.write(pdf)

        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'product_label_order_line.pdf')
        print_report(instance_path)

    def test_print_product_label_sale_show_origin_line_report(self):
        '''Print product label from sale with 'quantity' is 'line' and
        show_origin is True.'''
        wiz = self.env['wiz.product.label'].with_context(
            dict(active_ids=[self.order_01.id])).create({
                'quantity': 'line'})
        re = wiz.button_print_from_sale()
        ctx = re['context']
        ctx.update(
            dict(active_ids=[self.order_01.order_line], show_origin=True))

        def print_report(fname):
            pdf = self.env['report'].with_context(ctx).get_pdf(
                self.order_01.order_line,
                re['report_name'], data=re['datas'])
            with open(fname, 'w') as fp:
                fp.write(pdf)

        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'product_label_order_show_origin_line.pdf')
        print_report(instance_path)

    def test_print_product_label_sale_total_report(self):
        '''Print product label from sale with 'quantity' is 'total'.'''
        wiz = self.env['wiz.product.label'].with_context(
            dict(active_ids=[self.order_01.id])).create({
                'quantity': 'total'})
        re = wiz.button_print_from_sale()
        ctx = re['context']
        ctx.update(dict(active_ids=[self.order_01.order_line]))

        def print_report(fname):
            pdf = self.env['report'].with_context(ctx).get_pdf(
                self.order_01.order_line,
                re['report_name'], data=re['datas'])
            with open(fname, 'w') as fp:
                fp.write(pdf)

        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'product_label_order_total.pdf')
        print_report(instance_path)

    def test_print_product_label_sale_show_origin_total_report(self):
        '''Print product label from sale with 'quantity' is 'total' and
        show_origin is True.'''
        wiz = self.env['wiz.product.label'].with_context(
            dict(active_ids=[self.order_01.id])).create({
                'quantity': 'total'})
        re = wiz.button_print_from_sale()
        ctx = re['context']
        ctx.update(
            dict(active_ids=[self.order_01.order_line], show_origin=True))

        def print_report(fname):
            pdf = self.env['report'].with_context(ctx).get_pdf(
                self.order_01.order_line,
                re['report_name'], data=re['datas'])
            with open(fname, 'w') as fp:
                fp.write(pdf)

        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'product_label_order_show_origin_total.pdf')
        print_report(instance_path)
