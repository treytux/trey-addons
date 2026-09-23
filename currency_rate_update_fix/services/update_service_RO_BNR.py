# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
###############################################################################
from openerp.addons.currency_rate_update.services.currency_getter_interface \
    import Currency_getter_interface

from datetime import datetime, timedelta

import logging
import ssl
import urllib2

_logger = logging.getLogger(__name__)


class RO_BNR_getter(Currency_getter_interface):

    def get_url(self, url):
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_default_certs()
        opener = urllib2.build_opener(urllib2.HTTPSHandler(context=context))
        last_error = None
        for attempt in range(3):
            response = None
            try:
                response = opener.open(url, timeout=30)
                rawfile = response.read()
                if not rawfile:
                    raise IOError('BNR returned an empty XML document')
                return rawfile
            except (IOError, OSError, ssl.SSLError) as error:
                last_error = error
                _logger.warning(
                    'Unable to retrieve BNR rates (attempt %s/3): %s',
                    attempt + 1, error)
            finally:
                if response:
                    response.close()
        raise last_error

    def rate_retrieve(self, dom, ns, curr):
        res = {}
        xpath_rate_currency = "/def:DataSet/def:Body/def:Cube/def:Rate" + \
                              "[@currency='%s']/text()" % (curr.upper())
        xpath_rate_ref = "/def:DataSet/def:Body/def:Cube/def:Rate" + \
                         "[@currency='%s']/@multiplier" % (curr.upper())
        res['rate_currency'] = float(dom.xpath(
            xpath_rate_currency, namespaces=ns)[0])
        try:
            res['rate_ref'] = float(dom.xpath(
                xpath_rate_ref, namespaces=ns)[0])
        except Exception:
            res['rate_ref'] = 1
        return res

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days):
        url = 'https://curs.bnr.ro/nbrfxrates.xml'
        if main_currency in currency_array:
            currency_array.remove(main_currency)
        from lxml import etree
        _logger.debug("BNR currency rate service : connecting...")
        rawfile = self.get_url(url)
        dom = etree.fromstring(rawfile)
        adminch_ns = {'def': 'https://www.bnr.ro/xsd'}
        rate_date = dom.xpath(
            '/def:DataSet/def:Body/def:Cube/@date',
            namespaces=adminch_ns)[0]
        rate_date_datetime = datetime.strptime(rate_date, '%Y-%m-%d') + \
            timedelta(days=1)
        self.check_rate_date(rate_date_datetime, max_delta_days)
        self.supported_currency_array = dom.xpath(
            "/def:DataSet/def:Body/" + "def:Cube/def:Rate/@currency",
            namespaces=adminch_ns)
        self.supported_currency_array = [
            x.upper() for x in self.supported_currency_array]
        self.supported_currency_array.append('RON')
        self.validate_cur(main_currency)
        if main_currency != 'RON':
            main_curr_data = self.rate_retrieve(dom, adminch_ns, main_currency)
            main_rate = main_curr_data['rate_currency'] / \
                main_curr_data['rate_ref']
        for curr in currency_array:
            self.validate_cur(curr)
            if curr == 'RON':
                rate = main_rate
            else:
                curr_data = self.rate_retrieve(dom, adminch_ns, curr)
                if main_currency == 'RON':
                    rate = curr_data['rate_ref'] / curr_data['rate_currency']
                else:
                    rate = main_rate * curr_data['rate_ref'] / \
                        curr_data['rate_currency']
            self.updated_currency[curr] = rate
            _logger.debug(
                "BNR Rate retrieved : 1 " + main_currency + ' = ' + str(
                    rate) + ' ' + curr)
        return self.updated_currency, self.log_info
