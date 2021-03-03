# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    def setUp(self):
        super(TestProductTemplate, self).setUp()
        self.pt_unavailable = self.env['product.template'].create({
            'name': 'Unavailable product'})
        self.pt_available = self.env['product.template'].create({
            'name': 'Available product'})

    def test_substitution_product(self):
        self.pt_unavailable.substitution_product = self.pt_available
        self.assertEquals(
            self.pt_unavailable.substitution_product, self.pt_available)
