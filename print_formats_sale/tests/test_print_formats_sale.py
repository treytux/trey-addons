# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields, tools
import os
import logging
_log = logging.getLogger(__name__)


class TestPrintFormatsSale(common.TransactionCase):
    def setUp(self):
        super(TestPrintFormatsSale, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'CompanyCompany',
            'custom_header': True,
            'report_header': 'Yes! My company'})

        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'default_code': '123456'})

        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})

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
            'company_id': self.company.id,
            'client_order_ref': '016/81601863/ BM PALMA DE MALLORCA'})

        self.taxs_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.company.id})

        self.order_line_01 = self.env['sale.order.line'].create({
            'order_id': self.order_01.id,
            'name': 'Description 1',
            'product_uom_qty': 1,
            'price_unit': 33.25,
            'payment_term': self.ref(
                'account.account_payment_term_line_net'),
            'product_uom': self.ref('product.product_uom_unit'),
            'company_id': self.company.id,
            'tax_id': [(6, 0, [self.taxs_21.id])]})

    def print_report(self, obj, rname, fname):
        pdf = self.env['report'].get_pdf(obj, rname)
        with open(fname, 'w') as fp:
            fp.write(pdf)

    def test_print_formats_sale(self):
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'test_print_formats_sale_saleorder.pdf')
        self.print_report(
            self.order_01, 'sale.report_saleorder', instance_path)
