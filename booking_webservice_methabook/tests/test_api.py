# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp.addons.booking_webservice_methabook.models.methabook \
    import Methabook


class TestStringMethods(common.TransactionCase):
    def setUp(self):
        super(TestStringMethods, self).setUp()
        self.bw_methabook_booking = self.env.ref(
            'booking_webservice_methabook.bw_methabook_booking')
        self.bw_methabook_booking_test = self.env.ref(
            'booking_webservice_methabook.bw_methabook_booking_test')
        self.webservice = self.env['booking.webservice']
        self.api = Methabook(
            self.bw_methabook_booking_test.url,
            self.bw_methabook_booking_test.api_key)
        response = self.api.open_url(self.bw_methabook_booking_test.url)
        self.json_data = self.webservice.get_request_body(response)

    def check_and_detect(self, check_fiels, required=None):
        json_data, right_structure, loc = check_fiels
        for dict_item in json_data:
            struc_diff = set(right_structure) - set(dict_item.keys())
            if struc_diff:
                return True
            loc_diff = set(loc) - set(dict_item['Location'].keys())
            if loc_diff:
                return True
        return False

    def check_values(self, json_data, right_structure, required=None):
        for dict_item in json_data:
            conditions = not dict_item.keys().sort() == right_structure.sort()
            if required:
                not_allow = len(required) == 2 and required[1] or [
                    'null', "null", []]
                conditions = conditions or json_data[dict_item] in not_allow
            if conditions:
                return True
        return False

    def test_connect(self):
        methabook = Methabook(
            self.bw_methabook_booking.url, self.bw_methabook_booking.api_key)
        response = methabook.open_url(self.bw_methabook_booking.url)
        connection_ok = self.webservice.check_conection(response)
        self.assertTrue(connection_ok)

    def test_json_booking_structure(self):
        right_structure = [u'Zones', u'Customers', u'Track', u'Suppliers',
                           u'Bookings', u'ExportId', u'ExportedAt']
        self.assertTrue(self.json_data.keys().sort() == right_structure.sort())

    def test_json_customers_structure(self):
        customer_struc = [u'Account', u'Name', u'Phone', u'Location',
                          u'LegalName', u'Email', u'Vat']
        loc = [u'Province', u'City', u'Country', u'PostalCode', u'Address']
        flag = False
        flag = self.check_and_detect([
            self.json_data['Customers'], customer_struc, loc])
        self.assertFalse(flag)

    def test_json_suppliers_structure(self):
        supplier_struc = [u'Account', u'Name', u'FiscalName', u'Phone',
                          u'Email', u'Vat', u'Location']
        Loc = [u'Address', u'City', u'Province', u'Country', u'PostalCode']
        flag = False
        flag = self.check_and_detect(
            [self.json_data['Suppliers'], supplier_struc, Loc])
        self.assertFalse(flag)

    def test_json_zones_structure(self):
        zones_struc = [u'Code', u'Name', u'ParentZone']
        Loc = []
        flag = False
        flag = self.check_and_detect(
            [self.json_data['Zones'], zones_struc, Loc])
        self.assertFalse(flag)

    def test_update_or_create(self):
        bookings = self.json_data['Bookings']
        accomodation_zone = [u'Code', u'Name']
        flag = self.check_values(bookings, accomodation_zone)
        self.assertFalse(flag)
