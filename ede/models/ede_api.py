# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import random
import string
import logging
import requests
import urllib3
import xml.etree.cElementTree as et
_log = logging.getLogger(__name__)
try:
    from requests import Session
    from requests.auth import HTTPBasicAuth
    from zeep import Client
    from zeep.plugins import HistoryPlugin
    from zeep.settings import Settings
    from zeep.transports import Transport
    from zeep.helpers import serialize_object
except ImportError:
    _log.debug('Can not `import zeep`.')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
NS = {'soap': 'http://www.w3.org/2003/05/soap-envelope'}


class Ede(object):
    def __init__(self, wsdl, member, user, password, url_user, url_password):
        self.wsdl = wsdl
        self.member = member
        self.user = user
        self.password = password
        self.url_user = url_user
        self.url_password = url_password

    def connection(self):
        try:
            session = Session()
            session.auth = HTTPBasicAuth(self.url_user, self.url_password)
            session.verify = False
            settings = Settings(strict=False)
            transport = Transport(session=session)
            pluging = HistoryPlugin()
            return Client(self.wsdl, transport=transport, settings=settings,
                          plugins=[pluging])
        except RuntimeError as detail:
            _log.critical(
                'EDE Connector Critical Error', detail)
            raise

    def generate_string(self, length=20):
        letters_and_digits = string.ascii_letters + string.digits
        request_text = ''.join(
            random.choice(letters_and_digits) for i in range(length))
        return request_text

    def simulate_order(self, client, credentials=None, payload=None,
                       language='EN', version=1.92, action='ELC'):
        try:
            request_id = self.generate_string()
            simulate_order = client.service.simulateOrder(
                Credentials=credentials,
                Payload=payload,
                language=language,
                requestId=request_id,
                version=version,
                action=action,
            )
        except RuntimeError as detail:
            _log.critical(
                'EDE Connector Critical Error', detail)
            raise
        if simulate_order['StatusInformation'] != 'OK':
            return []
        return simulate_order._value_1

    def create_order(self, client, credentials=None, payload=None,
                     language='EN', version=1.92, action='ELC'):
        try:
            request_id = self.generate_string()
            put_order = serialize_object(
                client.service.createOrder(
                    Credentials=credentials,
                    Payload=payload,
                    language=language,
                    requestId=request_id,
                    version=version,
                    action=action,
                    )
            )
        except RuntimeError as detail:
            _log.critical(
                'EDE Connector Critical Error', detail)
            raise
        if put_order['StatusInformation'] != 'OK':
            return []
        return put_order['_value_1']

    def get_order_status(self, order_id=None):
        xml_data = self.get_xml_order_status(order_id)
        headers = {
            'Content-Type':
                'application/soap+xml; charset=utf-8; action="GetOrderStatus"',
            'SOAPAction': '"GetOrderStatus"'}

        try:
            get_order_status = requests.post(
                self.wsdl,
                data=xml_data,
                auth=(self.url_user, self.url_password),
                verify=False,
                headers=headers
            )
        except RuntimeError as detail:
            _log.critical(
                'EDE Connector Critical Error', detail)
            raise
        if get_order_status.status_code != 200:
            return False
        xpath = 'soap:Body/Response/Payload/GetOrderStatusConfirmation' \
                '/Protocol/Order'
        return et.fromstring(get_order_status.content).findall(xpath, NS)[0]

    def get_xml_order_status(
            self, order_id, language='EN', version=1.92, action='ELC'):
        soap = et.Element('soap:Envelope')
        soap.set('xmlns:soap', 'http://www.w3.org/2003/05/soap-envelope')
        et.SubElement(soap, 'soap:Header')
        body = et.SubElement(soap, 'soap:Body')
        order_status = et.SubElement(body, 'GetOrderStatusRequest')
        order_status.set('language', language)
        order_status.set('requestId', '1')
        order_status.set('version', str(version))
        order_status.set('action', action)
        login = et.SubElement(order_status, 'Credentials')
        et.SubElement(login, 'MemberId').text = self.member
        et.SubElement(login, 'Login').text = self.user
        et.SubElement(login, 'Password').text = self.password
        payload = et.SubElement(order_status, 'Payload')
        rng = et.SubElement(payload, 'Range')
        item = et.SubElement(rng, 'Item')
        item.set('type', 'document')
        et.SubElement(item, 'Sign').text = 'I'
        et.SubElement(item, 'Option').text = 'EQ'
        et.SubElement(item, 'Low').text = order_id
        et.SubElement(item, 'High').text = order_id
        et.SubElement(payload, 'GetTrackingDetails').text = '2'
        et.SubElement(payload, 'Itemlist').text = '1'
        return et.tostring(soap)


if __name__ == '__main__':
    _log.info('Open main method')
