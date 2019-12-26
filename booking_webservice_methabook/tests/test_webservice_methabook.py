# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import json
import os
from openerp.tests import common
#   from openerp import fields, exceptions, _
# from test_dummy_data import TestDummyData
import logging
_log = logging.getLogger(__name__)


class TestMetabookWebservice(common.TransactionCase):
    def setUp(self):
        super(TestMetabookWebservice, self).setUp()

    # def test_preload_zones(self):
    #     res = self.webservice.button_preload_booking_zones()
    #     self.assertTrue(res)

    # def test_connect(self):
    #     methabook = Methabook(
    #         self.bw_methabook_booking.url, self.bw_methabook_booking.api_key)
    #     response = methabook.open_url(self.bw_methabook_booking.url)
    #     connection_ok = self.webservice.check_conection(response)
    #     self.assertTrue(connection_ok)

    # def test_update_bookings_methabook(self):
    #     self.webservice = self.env['booking.webservice']
    #     res = self.webservice.update_bookings_methabook(test=True)
    #     _log.info('X' * 80)
    #     _log.info(('res', res))
    #     _log.info('X' * 80)
    #     self.assertFalse([], res)

    # def test_customer_unpaid(self):
    #     _log.info('X' * 80)
    #     _log.info(('entra'))
    #     _log.info('X' * 80)
    #     # No tiene saldo, limite researcg = True
    #     # (ya se se ha detectado, vuelve a no tener saldo)
    #     #     - si han pasado los dias indicados: notifica de nuevo:
    #     #     - si no han pasado los dias NOTHING
    #     self.partner_unpaid = self.env['res.partner'].create({
    #         'name': 'unpaid',
    #         'is_company': True,
    #         'customer': True,
    #         'credit_limit': 10.0,
    #         'customer_account_ref_methabook': '9999999',
    #         'credit_limit_reached': True,
    #         'credit_limit_reached_date': datetime.datetime.today(),
    #         'street': 'Calle Real, 33',
    #         'phone': '666225522'})
    #     self.create_and_pay_my_invoice(self.partner_unpaid)
    #     _log.info('X' * 80)
    #     _log.info(('self.partner_unpaid.credit', self.partner_unpaid.credit))
    #     _log.info('X' * 80)
    #     res = self.webservice.check_customer_credit_limit(
    #         self.partner_unpaid, True)
    #     self.assertFalse([], res)

    # def test_send_customer_credit_email(self):
    #     partner_unpaid = self.env['res.partner'].create({
    #         'name': 'unpaid',
    #         'is_company': True,
    #         'customer': True,
    #         'credit_limit': 10.0,
    #         'customer_account_ref_methabook': '9999999',
    #         'credit_limit_reached': True,
    #         'credit_limit_reached_date': datetime.datetime.today(),
    #         'street': 'Calle Real, 33',
    #         'phone': '666225522'})
    #     res = self.webservice.send_customer_credit_email(partner_unpaid)
    #     self.assertFalse([], res)

    # def test_first_load_bookings_json(self):
    #     self.webservice.first_load_bookings_json(test=True)

    # def test_send_customer_credit_email(self):
    #     self.webservice.first_load_bookings_json(test=True)

    def test_booking_methabook(self):
        def get_path(*relative_path):
            path = '../../tests/json_test'
            # path = '../../tests/octubre_json'
            fname = os.path.join(__file__, path, *relative_path)
            return os.path.abspath(fname)

        self.webservice = self.env['booking.webservice']
        # file_name = 'supplier_without_account_log_test.json'
        file_name = 'bookings_dicember_test.json'
        path = get_path(file_name)
        text_data = open(path, 'r').read()
        json_data = json.loads(text_data)['Export']
        # json_data = json.dumps()
        objects_processed, customers_list, suppliers_list, bookings_list = (
            self.webservice.booking_methabook(json_data))
        _log.info('X' * 80)
        _log.info(('objects_processed', objects_processed))
        _log.info(('customers_list', customers_list))
        _log.info(('suppliers_list', suppliers_list))
        _log.info(('bookings_list', bookings_list))
        _log.info('X' * 80)
        self.assertFalse([], objects_processed)
