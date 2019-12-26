# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
import logging
_log = logging.getLogger(__name__)


class TestNoDuplicates(common.TransactionCase):
    def setUp(self):
        super(TestNoDuplicates, self).setUp()

    def test_no_partners_duplicates(self):
        partners = self.env['res.partner'].search([
            ('customer', '=', True), ('supplier', '=', False)])
        partners_name_list = [p.name for p in partners]
        partners_name_list_set = list(set(partners_name_list))
        self.assertEqual(len(partners_name_list), len(partners_name_list_set))

    def test_no_suppliers_duplicates(self):
        suppliers = self.env['res.partner'].search([
            ('customer', '=', True), ('supplier', '=', True)])
        partners_name_list = [p.name for p in suppliers]
        partners_name_list_set = list(set(partners_name_list))
        self.assertEqual(len(partners_name_list), len(partners_name_list_set))

    def test_no_bookings_duplicates(self):
        bookings = self.env['booking'].search([('methabook_id', '!=', False)])
        booking_list = [p.name for p in bookings]
        booking_list_set = list(set(booking_list))
        self.assertEqual(len(booking_list), len(booking_list_set))
