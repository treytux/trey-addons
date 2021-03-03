###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import pprint

from odoo import http
from odoo.http import request
from werkzeug import utils

_log = logging.getLogger(__name__)


class OgoneController(http.Controller):
    _accept_url = '/payment/direct_order/feedback'

    @http.route(
        ['/payment/direct_order/feedback'],
        type='http', auth='none', csrf=False)
    def direct_order_form_feedback(self, **post):
        _log.info(
            'Beginning form_feedback with post data %s', pprint.pformat(post))
        request.env['payment.transaction'].sudo().form_feedback(
            post, 'direct_order')
        return utils.redirect(post.pop('return_url', '/'))
