# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields, tools
import os
import logging
_log = logging.getLogger(__name__)


class TestPrintReportPurchase(common.TransactionCase):

    def setUp(self):
        super(TestPrintReportPurchase, self).setUp()
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

        self.location = self.env['stock.location'].search([
            ('usage', '=', 'customer')], limit=1)[0]

        self.taxes_id = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company')})
        self.purchase_order_01 = self.env['purchase.order'].create({
            'pricelist_id': self.ref('product.list0'),
            'partner_id': self.partner_01.id,
            'section_id': self.ref('sales_team.section_sales_department'),
            'date_order': fields.Date.today(),
            'company_id': self.ref('base.main_company'),
            'location_id': self.location.id,
            'carrier_tracking_ref': 'aaaa',
            'payment_term': self.env.ref(
                'account.account_payment_term_line_net').id})

        self.purchase_line_01 = self.env['purchase.order.line'].create({
            'order_id': self.purchase_order_01.id,
            'name': 'Description 1',
            'price_unit': 33.25,
            'payment_term': self.ref(
                'account.account_payment_term_line_net'),
            'product_uom': self.ref('product.product_uom_unit'),
            'product_qty': 1})

    def test_print_purchase_report(self):
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'test_atrapada_customize_report_purchaseorder.pdf')
        self.print_report(
            self.purchase_order_01, 'purchase.report_purchaseorder',
            instance_path)
