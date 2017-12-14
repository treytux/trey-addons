# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import tools
import os


class TestPrintProductLabelReportPurchase(common.TransactionCase):
    def setUp(self):
        super(TestPrintProductLabelReportPurchase, self).setUp()
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'ean13': '8718833209409'})

    def print_report(self, obj, rname, fname):
        pdf = self.env['report'].get_pdf(obj, rname)
        with open(fname, 'w') as fp:
            fp.write(pdf)

    def test_print_product_label_purchasereport(self):
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'test_print_formats_product_label_purchase.pdf')
        self.print_report(
            self.pp_01, 'print_formats_product_label.label',
            instance_path)
