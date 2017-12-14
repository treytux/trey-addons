# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.addons.website_sale.controllers.main as main
from openerp import http, _


class WebsiteSale(main.website_sale):
    def _get_default_ppg(self):
        return 20

    def _get_default_order(self):
        return 'desc'

    def _get_default_order_by(self):
        return 'website_sequence'

    def _get_ppr_grid(self):
        return 4

    def _get_ppr_list(self):
        return 1

    def _get_ppg_values(self):
        return [10, 20, 50, 100]

    def _check_order_values(self, order, order_values):
        order_by_keys = [
            p['order_by'] for p in order_values] if order_values else []
        order_keys = [
            p['order'] for p in order_values] if order_values else []

        parts = order.split(' ')
        order_by_value = parts[0] if len(parts) > 0 else ''
        order_value = parts[1] if len(parts) > 1 else ''
        return (
            order_by_value if order_by_value in order_by_keys
            else self._get_default_order_by(),
            order_value if order_value in order_keys
            else self._get_default_order())

    @http.route()
    def shop(self, page=0, category=None, search='', **post):
        order_values = [
            {'name': _('Greater Relevancy'), 'order_by': 'website_sequence',
                'order': 'desc'},
            {'name': _('Lower Relevancy'), 'order_by': 'website_sequence',
                'order': 'asc'},
            {'name': _('Lower Price'), 'order_by': 'list_price',
                'order': 'asc'},
            {'name': _('Greater Price'), 'order_by': 'list_price',
                'order': 'desc'},
            {'name': _('Name A-Z'), 'order_by': 'name', 'order': 'asc'},
            {'name': _('Name Z-A'), 'order_by': 'name', 'order': 'desc'}]
        ppg = post.get('ppg', self._get_default_ppg())
        main.PPG = int(ppg)
        view = post.get('view', '')
        main.PPR = (
            self._get_ppr_list() if view == 'list' else self._get_ppr_grid())
        order_by, order = self._check_order_values(
            post.get('order', '%s %s' % (
                self._get_default_order_by(),
                self._get_default_order())), order_values)
        post['order'] = '%s %s' % (order_by, order)
        res = super(WebsiteSale, self).shop(
            page=page, category=category, search=search, **post)
        res.qcontext['order_values'] = order_values
        res.qcontext['order_by'] = order_by
        res.qcontext['order'] = order
        res.qcontext['ppg_values'] = self._get_ppg_values()
        res.qcontext['ppg'] = main.PPG
        res.qcontext['view'] = view
        res.qcontext['items_from'] = res.qcontext['pager']['offset'] + 1
        res.qcontext['items_to'] = (
            res.qcontext['pager']['offset'] + min(main.PPG, len(
                res.qcontext['products'])))
        res.qcontext['items_total'] = res.qcontext['pager']['total']
        return res
