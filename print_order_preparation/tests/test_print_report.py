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
        self.account_tax_obj = self.env['account.tax']
        self.partner_obj = self.env['res.partner']
        self.product_templ_obj = self.env['product.template']
        self.product_obj = self.env['product.product']

        # Common data
        self.taxs_21 = self.account_tax_obj.search([
            ('name', 'like', '%21%'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not self.taxs_21.exists():
            raise exceptions.Warning(_(
                'Does not exist any account tax with \'21\' in name.'))

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
        pt_01_data = {
            'name': 'Product 01',
            'type': 'product',
            'loc_rack': 'A001'}
        self.pt_01 = self.product_templ_obj.create(pt_01_data)
        pp_01_data = {
            'product_tmpl_id': self.pt_01.id,
            'default_code': '123456'}
        self.pp_01 = self.product_obj.create(pp_01_data)
        pt_02_data = {
            'name': 'Product 02',
            'type': 'product',
            'loc_rack': 'A002'}
        self.pt_02 = self.product_templ_obj.create(pt_02_data)
        pp_02_data = {
            'product_tmpl_id': self.pt_02.id,
            'default_code': '0078978'}
        self.pp_02 = self.product_obj.create(pp_02_data)

        self.order_obj = self.env['sale.order']
        self.order_line_obj = self.env['sale.order.line']

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
            'product_uom_qty': 1,
            'price_unit': 33.25,
            'product_uom': self.ref('product.product_uom_unit'),
            'tax_id': [(6, 0, [self.taxs_21[0].id])]}
        self.order_line_01 = self.order_line_obj.create(order_line_01_data)
        order_line_02_data = {
            'order_id': self.order_01.id,
            'product_id': self.pp_02.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
            'tax_id': [(6, 0, [self.taxs_21[0].id])]}
        self.order_line_02 = self.order_line_obj.create(order_line_02_data)
        order_line_03_data = {
            'order_id': self.order_01.id,
            'product_id': self.pp_01.id,
            'product_uom_qty': 3,
            'product_uom': self.ref('product.product_uom_unit'),
            'tax_id': [(6, 0, [self.taxs_21[0].id])]}
        self.order_line_03 = self.order_line_obj.create(order_line_03_data)

    def print_report(self, obj, rname, fname):
        pdf = self.env['report'].get_pdf(obj, rname)
        with open(fname, 'w') as fp:
            fp.write(pdf)

    def test_print_sale_order_report(self):
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'report_order_preparation.pdf')
        self.print_report(
            self.order_01, 'print_order_preparation.report_order_preparation',
            instance_path)
