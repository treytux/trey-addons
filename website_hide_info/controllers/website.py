# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp.addons.website.controllers import main
from openerp import http
from openerp.http import request
import logging
_log = logging.getLogger(__name__)


class WebsiteHideInfo(main.Website):
    @http.route('/website/info', type='http', auth="public", website=True)
    def website_info(self):
        super(WebsiteHideInfo, self).website_info()
        return request.website.render('website.404')
