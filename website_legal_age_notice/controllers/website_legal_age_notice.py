# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import http


class LegalAgeNotice(http.Controller):
    @http.route('/website_legal_age_notice/yes', auth='public', type='http')
    def accept_legal_age(self):
        http.request.session['accepted_legal_age'] = True
        return http.local_redirect('/')
