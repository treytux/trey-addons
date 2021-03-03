###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime
import logging
import os
import xml.etree.cElementTree as et

import requests
import urllib3
from requests import Session
from requests.auth import HTTPBasicAuth

_log = logging.getLogger(__name__)
try:
    from zeep import Client
    from zeep.plugins import HistoryPlugin
    from zeep.settings import Settings
    from zeep.transports import Transport
    from zeep.helpers import serialize_object
except ImportError:
    _log.debug('Can not `import zeep`.')

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings()
NS = {'soap': 'http://www.w3.org/2003/05/soap-envelope'}


class EdeApi(object):
    def __init__(self, wsdl, member, user, password, url_user, url_password):
        self.wsdl = wsdl
        self.member = member
        self.user = user
        self.password = password
        self.url_user = url_user
        self.url_password = url_password
        self.language = 'EN'
        self.version = 1.92
        self.action = 'ELC'

    def wsd_connection(self):
        try:
            session = Session()
            session.auth = HTTPBasicAuth(self.url_user, self.url_password)
            session.verify = False
            settings = Settings(strict=False)
            transport = Transport(session=session)
            pluging = HistoryPlugin()
            return Client(
                self.wsdl, transport=transport, settings=settings,
                plugins=[pluging])
        except RuntimeError as detail:
            _log.critical('EDE Connector Critical Error', detail)

    def generate_string(self):
        return ''.join([datetime.datetime.now().strftime('%y%m%d%H%M%S%f'),
                        str(os.getpid()).zfill(20 - 15), ])[:20]

    def simulate_order(self, client, credentials=None, payload=None):
        try:
            request_id = self.generate_string()
            simulate_order = client.service.simulateOrder(
                Credentials=credentials,
                Payload=payload,
                language=self.language,
                requestId=request_id,
                version=self.version,
                action=self.action,
            )
        except RuntimeError as detail:
            _log.critical('EDE Connector Critical Error', detail)
            raise
        if simulate_order['StatusInformation'] != 'OK':
            return []
        return simulate_order._value_1

    def create_order(self, client, credentials=None, payload=None):
        try:
            request_id = self.generate_string()
            put_order = serialize_object(client.service.createOrder(
                Credentials=credentials,
                Payload=payload,
                language=self.language,
                requestId=request_id,
                version=self.version,
                action=self.action,
            ))
        except RuntimeError as detail:
            _log.critical('EDE Connector Critical Error', detail)
            raise
        if put_order['StatusInformation'] != 'OK':
            return []
        return put_order['_value_1']

    def get_order_status(self, order_id=None):
        xml_data = self.get_xml_order_status(order_id)
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8; '
                            'action="GetOrderStatus"',
            'SOAPAction': '"GetOrderStatus"'
        }
        try:
            get_order_status = requests.post(
                self.wsdl,
                data=xml_data,
                auth=(self.url_user, self.url_password),
                verify=False,
                headers=headers,
            )
        except RuntimeError as detail:
            _log.critical(
                'EDE Connector Critical Error', detail)
            raise
        if get_order_status.status_code != 200:
            return False
        xpath = (
            'soap:Body/Response/Payload/GetOrderStatusConfirmation'
            '/Protocol/Order')
        orders = et.fromstring(get_order_status.content).findall(xpath, NS)
        if orders:
            return orders[0]
        _log.critical('EDE Connector Order Status no Data: %s' % order_id)
        return False

    def get_xml_order_status(self, order_id, ):
        soap = et.Element('soap:Envelope')
        soap.set('xmlns:soap', 'http://www.w3.org/2003/05/soap-envelope')
        et.SubElement(soap, 'soap:Header')
        body = et.SubElement(soap, 'soap:Body')
        order_status = et.SubElement(body, 'GetOrderStatusRequest')
        order_status.set('language', self.language)
        order_status.set('requestId', '1')
        order_status.set('version', str(self.version))
        order_status.set('action', self.action)
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
