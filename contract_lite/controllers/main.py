###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class PortalContractLite(CustomerPortal):
    def _get_recurring_rule_labels(self):
        return {
            'day': _('Days'),
            'daily': _('Days'),
            'week': _('Weeks'),
            'weekly': _('Weeks'),
            'month': _('Months'),
            'monthly': _('Months'),
            'quarter': _('Quarters'),
            'quarterly': _('Quarters'),
            'four_month': _('Four-month periods'),
            'four_monthly': _('Four-month periods'),
            'semester': _('Semesters'),
            'semesterly': _('Semesters'),
            'year': _('Years'),
            'yearly': _('Years'),
        }

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'contract_lite_count' in counters:
            contract_model = request.env['contract_lite.contract']
            contract_count = (
                contract_model.search_count([])
                if contract_model.check_access_rights(
                    'read',
                    raise_exception=False,
                )
                else 0
            )
            values['contract_lite_count'] = contract_count
        return values

    def _contract_lite_get_page_view_values(
            self, contract, access_token, **kwargs):
        values = {
            'page_name': 'contract_lite',
            'contract_lite': contract,
            'recurring_rule_labels': self._get_recurring_rule_labels(),
        }
        return self._get_page_view_values(
            contract, access_token, values, 'my_contract_lite_history', False,
            **kwargs)

    @http.route(
        ['/my/contracts-lite', '/my/contracts-lite/page/<int:page>'],
        type='http', auth='user', website=True)
    def portal_my_contract_lite(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        contract_obj = request.env['contract_lite.contract']
        if not contract_obj.check_access_rights('read', raise_exception=False):
            return request.redirect('/my')
        domain = []
        searchbar_sortings = {
            'name': {'label': _('Name'), 'order': 'name asc'},
            'date': {'label': _('Date'), 'order': 'recurring_next_date asc'},
            'code': {'label': _('Reference'), 'order': 'code asc'},
        }
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']
        contract_count = contract_obj.search_count(domain)
        pager = portal_pager(
            url='/my/contracts-lite',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
            },
            total=contract_count, page=page, step=self._items_per_page)
        contracts = contract_obj.search(
            domain, order=order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_contract_lite_history'] = contracts.ids[:100]
        values.update({
            'date': date_begin,
            'contracts': contracts,
            'contract_lite': False,
            'page_name': 'contract_lite',
            'pager': pager,
            'default_url': '/my/contracts-lite',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render('contract_lite.portal_my_contracts', values)

    @http.route(
        ['/my/contracts-lite/<int:contract_id>'],
        type='http',
        auth='public',
        website=True,
    )
    def portal_my_contract_lite_detail(
            self, contract_id, access_token=None, **kw,):
        try:
            contract_sudo = self._document_check_access(
                'contract_lite.contract', contract_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._contract_lite_get_page_view_values(
            contract_sudo, access_token, **kw
        )
        return request.render(
            'contract_lite.portal_contract_lite_page', values)
