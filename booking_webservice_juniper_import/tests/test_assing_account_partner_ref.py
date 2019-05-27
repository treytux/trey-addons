# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
import os


class TestAssingAccountPartnerRef(common.TransactionCase):
    def setUp(self):
        super(TestAssingAccountPartnerRef, self).setUp()
        self.juniper_webservice = self.env['booking.webservice'].create({
            'name': 'Test Local Juniper Booking',
            'type': 'juniper',
            'url': 'http://localhost:8080/complete_no_zones',
            'username': 'info@trey.es',
            'api_key': 'SNlyUPJlOIV1rZeCVuXJL4a3YNT1D8jl',
            'password': 'admin'})

        self.customer_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'customer_account_ref_methabook': 12222,
            'street': 'Calle Real, 33',
            'phone': '666225522'})
        self.customer_02 = self.env['res.partner'].create({
            'name': 'Customer 02',
            'is_company': True,
            'customer': True,
            'property_product_pricelist': None,
            'email': 'customer2@test.com',
            'street': 'Calle Sol, 1',
            'phone': '666777777'})
        self.supplier_01 = self.env['res.partner'].create({
            'name': 'Supplier 01',
            'is_company': True,
            'supplier': True,
            'email': 'supplier1@test.com',
            'street': 'Plaza General, 2',
            'supplier_account_ref_methabook': 13333,
            'phone': '666888999'})
        self.supplier_02 = self.env['res.partner'].create({
            'name': 'Supplier 02',
            'is_company': True,
            'supplier': True,
            'property_product_pricelist_purchase': None,
            'email': 'supplier2@test.com',
            'street': 'Avda Libertad, 6',
            'phone': '666778877'})

    def test_file_without_1_account_assinged(self):
        def get_path(*relative_path):
            path = '../'
            fname = os.path.join(__file__, path, *relative_path)
            return os.path.abspath(fname)

        file_name = 'test_import_account_partner_ref.xls'
        path = get_path(file_name)
        ffile = open(path, 'r').read()

        wiz = self.env['wizard.assing.partner.account.ref'].with_context({
            'active_ids': [self.juniper_webservice.id],
            'active_model': 'booking.webservice',
            'active_id': self.juniper_webservice.id}).create({'ffile': path})

        self.assertRaises(Exception, wiz.assing_partner_account_ref(ffile))
        self.assertEquals(int(self.supplier_01.supplier_account_ref), 999999)
        self.assertEquals(int(self.customer_01.customer_account_ref), 888888)
        wiz.unlink()
