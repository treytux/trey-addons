###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, http
from odoo.addons.portal.controllers.portal import get_records_pager
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

try:
    from odoo.addons.sale.controllers.portal import CustomerPortal
except ImportError:
    from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    def _prepare_quotations_domain(self, partner):
        domain = super()._prepare_quotations_domain(partner)
        domain.append(('is_return', '=', False))
        return domain

    def _prepare_orders_domain(self, partner):
        domain = super()._prepare_orders_domain(partner)
        domain.append(('is_return', '=', False))
        return domain

    def _get_rma_product_types(self):
        return ['product', 'consu']

    def _get_lines_domain(self, partner, search):
        products = request.env['product.product'].search([
            ('name', 'ilike', search),
            ('type', 'in', self._get_rma_product_types()),
        ])
        return [
            ('product_id', 'in', products.ids),
            ('state', 'in', ['sale', 'done']),
            ('order_partner_id', 'child_of', partner.commercial_partner_id.id),
            ('is_return', '=', False),
        ]

    def _inject_order_search_domain(self, domain, partner, search):
        if not search:
            return domain
        lines_domain = self._get_lines_domain(partner, search)
        order_lines = request.env['sale.order.line'].search(lines_domain)
        order_ids = list(set(order_lines.mapped('order_id').ids))
        if order_ids:
            return domain + [
                '|',
                ('name', 'ilike', search),
                ('id', 'in', order_ids),
            ]
        return domain + [('name', 'ilike', search)]

    def _get_sale_return_domain(self, partner, search=False):
        domain = [
            (
                'message_partner_ids',
                'child_of',
                [partner.commercial_partner_id.id]
            ),
            ('state', 'in', ['draft', 'sent', 'sale', 'done']),
            ('is_return', '=', True),
        ]
        return self._inject_order_search_domain(domain, partner, search)

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'return_count' not in counters:
            return values
        sale_order = request.env['sale.order']
        if sale_order.check_access_rights('read', raise_exception=False):
            partner = request.env.user.partner_id
            values['return_count'] = sale_order.search_count(
                self._get_sale_return_domain(partner))
        else:
            values['return_count'] = 0
        return values

    @http.route()
    def portal_my_orders(self, **kwargs):
        response = super().portal_my_orders(**kwargs)
        if not hasattr(response, 'qcontext'):
            return response
        partner = request.env.user.partner_id
        search = (kwargs.get('search') or '').strip()
        domain = self._prepare_orders_domain(partner)
        domain = self._inject_order_search_domain(domain, partner, search)
        date_begin = kwargs.get('date_begin')
        date_end = kwargs.get('date_end')
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        sortby = kwargs.get('sortby') or response.qcontext.get('sortby')
        if not sortby:
            sortby = 'date'
        searchbar_sortings = response.qcontext.get('searchbar_sortings', {})
        sort_order = searchbar_sortings.get(sortby, {}).get(
            'order', 'date_order desc')
        page = int(kwargs.get('page', 1))
        sale_order = request.env['sale.order']
        order_count = sale_order.search_count(domain)
        pager = portal_pager(
            url='/my/orders',
            total=order_count,
            page=page,
            step=self._items_per_page,
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'search': search,
                'sortby': sortby,
            }
        )
        orders = sale_order.search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_orders_history'] = orders.ids[:100]
        response.qcontext.update({
            'orders': orders.sudo(),
            'pager': pager,
            'search': search,
        })
        return response

    @http.route()
    def portal_order_page(
            self, order_id, report_type=None, access_token=None, message=False,
            download=False, **kw):
        response = super().portal_order_page(
            order_id=order_id, report_type=report_type,
            access_token=access_token, message=message, download=download, **kw)
        if report_type in ('html', 'pdf', 'text'):
            return response
        if not hasattr(response, 'qcontext'):
            return response
        order = response.qcontext.get('sale_order')
        if order and not order.is_return:
            response.qcontext['return_orders'] = (
                request.env['sale.order'].sudo().search([
                    ('parent_sale_order', '=', order_id),
                    ('is_return', '=', True),
                    ('state', '!=', 'cancel'),
                ])
            )
        return response

    def rma_form_validate(self, data, lines):
        errors = {}
        empty_order = True
        for idx, line in enumerate(lines):
            value = data.get(str(line.id))
            notes = data.get(f'notes-{line.id}')
            try:
                value = int(value)
            except (TypeError, ValueError):
                errors.setdefault(idx, {
                    'msg': _(
                        'Please provide integer numbers, not "%s"'
                    ) % (value or ''),
                    'product': line,
                })
                continue
            if value > 0:
                empty_order = False
                if not notes:
                    errors.setdefault(idx, {
                        'msg': _('Reason for return is mandatory'),
                        'product': line,
                    })
            if value > line.product_uom_qty:
                errors.setdefault(idx, {
                    'msg': _('Return quantity exceeds the ordered'),
                    'product': line,
                })
            if value < 0:
                errors.setdefault(idx, {
                    'msg': _('The amount to be returned cannot be negative'),
                    'product': line,
                })
            return_lines = request.env['sale.order.line'].sudo().search([
                ('parent_sale_order_line', '=', line.id),
                ('product_id', '=', line.product_id.id),
            ])
            qty_returned = sum(return_lines.mapped('product_uom_qty'))
            max_qty = int(line.product_uom_qty - qty_returned)
            if value > (line.product_uom_qty - qty_returned):
                errors.setdefault(idx, {
                    'msg': _('Max quantity to return exceeded: %s,') % max_qty,
                    'product': line,
                })
        if empty_order:
            errors.setdefault(-1, {
                'msg': _('You should select almost one product'),
                'product': None,
            })
        return errors

    @http.route(
        ['/my/orders/pdf/print-label/<int:order_id>'],
        type='http', auth='user', website=True)
    def print_address_label(self, order_id, access_token=None, **kw):
        order = self._document_check_access(
            'sale.order', order_id, access_token=access_token)
        report = request.env['ir.actions.report'].sudo()
        pdf = report._render_qweb_pdf(
            'website_rma.action_report_address_label',
            [order.id])[0]
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=headers)

    @http.route(
        ['/my/order/rma/<int:order>'], type='http', auth='user', website=True)
    def portal_order_rma(self, order, access_token=None, **post):
        order = self._document_check_access(
            'sale.order', order, access_token=access_token)
        order_line_obj = request.env['sale.order.line']
        lines = order.order_line.filtered(
            lambda line: line.product_id.type
            in order_line_obj._returnable_product_types()
            and line.product_id.is_returnable
        )
        values = self._prepare_portal_layout_values()
        values.update({
            'errors': {},
            'order': order,
            'order_lines': lines,
            'page_name': 'new_rma',
        })
        if post:
            errors = self.rma_form_validate(post, lines)
            values['errors'] = errors
            values.update(post)
            if not errors:
                return_order = order.copy({
                    'is_return': True,
                    'order_line': False,
                    'parent_sale_order': order.id,
                    'website_id': False,
                })
                return_order.message_subscribe(partner_ids=order.partner_id.ids)
                for order_line in lines:
                    qty_return = int(post[str(order_line.id)])
                    notes = post[f'notes-{order_line.id}']
                    if not qty_return:
                        continue
                    order_line.qty_return += qty_return
                    order_line.copy({
                        'is_return': True,
                        'notes': notes,
                        'order_id': return_order.id,
                        'parent_sale_order_line': order_line.id,
                        'product_uom_qty': qty_return,
                    })
                template = request.env.ref('website_rma.email_template_rma')
                template.sudo().with_context(
                    lang=request.env.user.lang,
                ).send_mail(return_order.id, force_send=True)
                request.website.sale_reset()
                request.session.update({'sale_last_order_id': False})
                return request.redirect(f'/my/orders/{order.id}')
        return request.render('website_rma.portal_order_rma', values)

    @http.route(
        ['/my/returns', '/my/returns/page/<int:page>'],
        type='http', auth='user', website=True)
    def portal_my_returns(self, page=1, date_begin=None, date_end=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        search = (kw.get('search') or '').strip()
        domain = self._get_sale_return_domain(partner, search)
        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }
        sortby = kw.get('sortby') or 'date'
        sort_order = searchbar_sortings[sortby]['order']
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        sale_order = request.env['sale.order']
        order_count = sale_order.search_count(domain)
        pager = portal_pager(
            url='/my/returns', total=order_count, page=page,
            step=self._items_per_page,
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'search': search,
                'sortby': sortby,
            }
        )
        return_orders = sale_order.search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_returns_history'] = return_orders.ids[:100]
        values.update({
            'date': date_begin,
            'return_orders': return_orders.sudo(),
            'page_name': 'returns',
            'pager': pager,
            'archive_groups': [],
            'default_url': '/my/returns',
            'search': search,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render('website_rma.portal_my_returns', values)

    @http.route(
        ['/my/returns/<int:return_id>'], type='http', auth='user', website=True)
    def portal_return_page(self, return_id, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access(
                'sale.order', return_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = {
            'sale_return': order_sudo,
            'page_name': 'sale_return',
            'partner_id': order_sudo.partner_id.id,
        }
        if order_sudo.company_id:
            values['res_company'] = order_sudo.company_id
        history = request.session.get('my_returns_history', [])
        values.update(get_records_pager(history, order_sudo))
        return request.render('website_rma.sale_return_portal_template', values)
