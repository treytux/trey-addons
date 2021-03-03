###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import http
from odoo.addons.website.controllers.main import Website

_logger = logging.getLogger(__name__)

try:
    import requests
except (ImportError, IOError) as err:
    _logger.debug(err)


class Website(Website):
    @http.route(
        ['/get_tracking_info_integra2'], type='json', auth='public',
        methods=['post'], website=True)
    def get_tracking_info_integra2(self, url):
        return requests.get(url).text
