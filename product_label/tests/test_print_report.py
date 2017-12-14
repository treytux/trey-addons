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

        # Create products
        self.product_01 = self.product_obj.create({
            'name': 'Product 01',
            'ean13': '0075678164125',
            'default_code': 'COD-PROD-1'})
        self.product_02 = self.product_obj.create({
            'name': 'Product 02',
            'default_code': 'COD-PROD-2'})

    def print_report(self, obj, rname, fname):
        pdf = self.env['report'].get_pdf(obj, rname)
        with open(fname, 'w') as fp:
            fp.write(pdf)

    def test_print_product_with_ean_report(self):
        '''Print product label with ean code.'''
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'product_label_with_ean.pdf')
        self.print_report(
            self.product_01, 'product_label.label', instance_path)

    def test_print_product_without_ean_report(self):
        '''Print product label without ean code.'''
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'product_label_without_ean.pdf')
        self.print_report(
            self.product_02, 'product_label.label', instance_path)
