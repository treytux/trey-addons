# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.tests.common as common


class TestEdifactSaleOrder(common.TransactionCase):

    def setUp(self):
        super(TestEdifactSaleOrder, self).setUp()
        self.edifact_document1 = self.env['edifact.document'].create({
            'name': 'test',
            'ttype': 'voucher'})

    def test_process_voucher_in_files(self):
        edi_doc = self.edifact_document1.process_process_voucher_in_files()
        self.assertTrue(edi_doc)
