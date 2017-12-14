# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import logging
import pprint
import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)


class OgoneController(http.Controller):
    _accept_url = '/payment/direct_order/feedback'

    @http.route(['/payment/direct_order/feedback'], type='http', auth='none')
    def transfer_form_feedback(self, **post):
        cr, uid, context = request.cr, SUPERUSER_ID, request.context
        _logger.info(
            'Beginning form_feedback with post data %s', pprint.pformat(post))
        request.registry['payment.transaction'].form_feedback(
            cr, uid, post, 'direct_order', context)
        return werkzeug.utils.redirect(post.pop('return_url', '/'))
