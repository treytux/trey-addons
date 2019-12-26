# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.tests.common as common
from openerp.modules.module import get_module_resource


class TestEdifact(common.TransactionCase):

    def get_dir_file_path(self, filename):
        path = get_module_resource('edifact',
                                   'tests', 'data', filename)
        path = path.replace((''.join(['/', filename])), '')
        return path

    def setUp(self):
        super(TestEdifact, self).setUp()
        self.edifact_document1 = self.env['edifact.document'].create({
            'name': 'test',
            'ttype': 'order'})
        self.path = self.get_dir_file_path('order.edi')

    def test_edifact_directory_structure(self):
        files = self.edifact_document1.ls_files(self.path)
        self.assertTrue(len(files))

    def test_edifact(self):
        files = self.edifact_document1.ls_files(self.path)
        for file in files:
            structure = self.edifact_document1.read_from_file(file)
        self.assertTrue(isinstance(structure, list))
