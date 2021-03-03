###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import xml.etree.cElementTree as et

import urllib3
from requests import Session
from requests.auth import HTTPBasicAuth

_log = logging.getLogger(__name__)
try:
    from zeep import Client
    from zeep.plugins import HistoryPlugin
    from zeep.settings import Settings
    from zeep.transports import Transport
    from dict2xml import dict2xml
except ImportError:
    _log.debug('Can not `import zeep`.')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
NS = {'soap': 'http://www.w3.org/2003/05/soap-envelope'}


class TermoClubApi(object):
    def __init__(self, wsdl, user, password):
        self.wsdl = wsdl
        self.user = user
        self.password = password

    def connection(self):
        try:
            session = Session()
            session.auth = HTTPBasicAuth(self.user, self.password)
            session.verify = False
            settings = Settings(strict=False)
            transport = Transport(session=session)
            pluging = HistoryPlugin()
            return Client(
                self.wsdl, transport=transport, settings=settings,
                plugins=[pluging])
        except RuntimeError as detail:
            _log.critical('TermoClub Connector Critical Error', detail)
            raise

    def get_product(self, client, product=None):
        try:
            get_product = client.service.ConsArt(
                pUsu=self.user,
                pPas=self.password,
                pCODART=product,
            )
        except RuntimeError as detail:
            _log.critical('TermoClub Connector Critical Error', detail)
            raise
        # return et.fromstring(get_product)

        return et.fromstring('%s%s%s' % ('<root>', get_product, '</root>'))

    def put_order(self, client, order=None):
        try:
            put_order = client.service.CapturaPedido(
                pUsu=self.user,
                pPas=self.password,
                pPed=dict2xml(order, indent='  '),
            )
        except RuntimeError as detail:
            _log.critical('TermoClub Connector Critical Error', detail)
            raise
        return et.fromstring('%s%s%s' % ('<root>', put_order, '</root>'))
