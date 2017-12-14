# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from test_print_report import TestPrintReport
from openerp import tools
import os


class TestPrintReportProductLabelComposition(TestPrintReport):

    def setUp(self):
        super(TestPrintReportProductLabelComposition, self).setUp()

    def test_print_product_label_composition_report(self):
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'test_print_formats_product_label_composition.pdf')
        self.print_report(
            self.pp_01,
            'print_formats_product_label_composition.composition_label',
            instance_path)
