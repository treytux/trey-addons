###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request, route


class CustomerPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Agreement = request.env['agreement']
        agreement_count = Agreement.search_count([
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
            'agreement_count': agreement_count,
        })
        return values

    @route()
    def home(self, **kw):
        res = super().home(**kw)
        res.qcontext['agreement_pending_count'] = 5
        return res

    @route(
        ['/my/agreements', '/my/agreements/page/<int:page>'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_my_agreements(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Agreement = request.env['agreement']
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
        archive_groups = self._get_archive_groups('agreement', domain)
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        agreement_count = Agreement.search_count(domain)
        pager = portal_pager(
            url='/my/agreements',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby
            },
            total=agreement_count,
            page=page,
            step=self._items_per_page
        )
        agreements = Agreement.search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_agreements_history'] = agreements.ids[:100]
        values.update({
            'date': date_begin,
            'agreements': agreements.sudo(),
            'page_name': 'agreement',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/agreements',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render(
            'portal_agreements.portal_my_agreements', values)

    def _agreement_get_page_view_values(self, agreement, **kwargs):
        values = {
            'page_name': 'agreement',
            'agreement': agreement,
            'user': request.env.user
        }
        return self._get_page_view_values(
            agreement, False, values, 'my_agreements_history', False,
            **kwargs)

    @http.route(
        ['/my/agreement/<int:agreement_id>'], type='http', auth='user',
        website=True, csrf=False)
    def portal_my_agreement(self, agreement_id, **kw):
        agreement = request.env['agreement'].browse(agreement_id)
        values = self._agreement_get_page_view_values(agreement.sudo(), **kw)
        return request.render('portal_agreements.portal_my_agreement', values)
