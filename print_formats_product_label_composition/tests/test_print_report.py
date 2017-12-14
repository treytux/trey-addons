# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common


class TestPrintReport(common.TransactionCase):

    def setUp(self):
        super(TestPrintReport, self).setUp()

        self.pt_01 = self.env['product.template'].create({
            'name': 'Producto Test',
            'type': 'consu'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'ean13': '8718833209409'})

    def print_report(self, obj, rname, fname):
        pdf = self.env['report'].get_pdf(obj, rname)
        with open(fname, 'w') as fp:
            fp.write(pdf)
