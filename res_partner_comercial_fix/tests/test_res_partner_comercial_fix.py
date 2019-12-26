# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common


class TestResPartnerComercialFix(common.TransactionCase):

    def setUp(self):
        super(TestResPartnerComercialFix, self).setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Partner 1',
            'comercial': 'Comercial name 1',
            'child_ids': [
                (0, 0, {'name': 'Contact 1.1'}),
                (0, 0, {'name': 'Contact 1.2'})]})
        self.assertEqual(
            self.partner_01.display_name, '(Comercial name 1) Partner 1')
        self.assertEqual(
            self.partner_01.child_ids[0].display_name,
            'Partner 1, Contact 1.1')
        self.assertEqual(
            self.partner_01.child_ids[1].display_name,
            'Partner 1, Contact 1.2')

    def test_change_comercial(self):
        self.partner_01.comercial = 'New comercial name'
        self.assertEqual(
            self.partner_01.display_name, '(New comercial name) Partner 1')
        self.assertEqual(
            self.partner_01.child_ids[0].display_name,
            'Partner 1, Contact 1.1')
        self.assertEqual(
            self.partner_01.child_ids[1].display_name,
            'Partner 1, Contact 1.2')

    def test_change_partner_01_name(self):
        self.partner_01.name = 'Customer 1'
        self.assertEqual(
            self.partner_01.display_name, '(Comercial name 1) Customer 1')
        self.assertEqual(
            self.partner_01.child_ids[0].display_name,
            'Customer 1, Contact 1.1')
        self.assertEqual(
            self.partner_01.child_ids[1].display_name,
            'Customer 1, Contact 1.2')
