###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request


class CustomerPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Contract = request.env['contract.contract']
        contract_count = Contract.search_count([
            '|',
            (
                'message_partner_ids',
                'child_of',
                [partner.commercial_partner_id.id],
            ),
            (
                'partner_id',
                '=',
                partner.commercial_partner_id.id,
            ),
        ])
        values.update({
            'contract_count': contract_count,
        })
        return values

    @http.route(
        ['/my/contracts', '/my/contracts/page/<int:page>'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_my_contracts(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Contract = request.env['contract.contract']
        domain = [
            '|',
            (
                'message_partner_ids',
                'child_of',
                [partner.commercial_partner_id.id],
            ),
            (
                'partner_id',
                '=',
                partner.commercial_partner_id.id,
            ),
        ]
        searchbar_sortings = {
            'name': {'label': _('Title'), 'order': 'name'},
            # 'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            # 'stage': {'label': _('Stage'), 'order': 'state'},
        }
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']
        archive_groups = self._get_archive_groups('contract.contract', domain)
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        contract_count = Contract.search_count(domain)
        pager = portal_pager(
            url='/my/contracts',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby
            },
            total=contract_count,
            page=page,
            step=self._items_per_page
        )
        contracts = Contract.search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_contracts_history'] = contracts.ids[:100]
        values.update({
            'date': date_begin,
            'contracts': contracts.sudo(),
            'page_name': 'contract',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/contracts',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render(
            'portal_contract.portal_my_contracts', values)
