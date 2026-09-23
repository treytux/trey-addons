# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
###############################################################################
import openerp.http as http


class WebsiteCookiebot(http.Controller):
    @http.route('/legal/cookies-policy', type='http', auth='user',
                website=True)
    def show_cookieboot_page(self, **kw):
        return http.request.render('website_cookiebot.cookies_policy', {})
