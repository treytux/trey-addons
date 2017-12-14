# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import http
from openerp.http import request
import logging
_log = logging.getLogger(__name__)
try:
    from openerp.addons.website_myaccount.controllers.main import MyAccount
except ImportError:
    MyAccount = object
    _log.error('No module named website_myaccount')


class MyAccountTrainingPlan(MyAccount):
    def _prepare_products(self, limit=None):
        env = request.env
        products = []
        domain = [
            '|',
            ('partner_id', 'in', self._get_partner_ids()),
            ('message_follower_ids', 'in', self._get_follower_ids())]
        invoices = env['account.invoice'].sudo().search(
            domain, limit=limit)
        if invoices:
            for i in invoices:
                for l in i.invoice_line:
                    if l.product_id.product_template_training_ids:
                        products.append(l.product_id.product_tmpl_id)
        return products

    @http.route([
        '/my/courses',
        '/myaccount/courses',
        '/mis/cursos',
        '/micuenta/cursos'
    ], type='http', auth='user', website=True)
    def products(self, container=None, **post):
        products = self._prepare_products()
        return request.website.render(
            'website_myaccount_training_plan.courses',
            {'products': products})
