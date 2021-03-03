###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request


class CustomerPortal(CustomerPortal):
    def _get_sale_quotation_domain(self, search=False):
        partner_id = request.env.user.partner_id.commercial_partner_id.id
        domain = [
            ('message_partner_ids', 'child_of', partner_id),
            ('state', 'in', ['sent', 'cancel']),
            ('is_return', '=', False),
        ]
        if search:
            domain.insert(0, '&')
            domain += [('name', 'ilike', search)]
        return domain

    def _get_sale_order_domain(self, search=False):
        partner_id = request.env.user.partner_id.commercial_partner_id.id
        domain = [
            ('message_partner_ids', 'child_of', partner_id),
            ('state', 'in', ['sale', 'done']),
            ('is_return', '=', False),
        ]
        if search:
            domain.insert(0, '&')
            domain += [('name', 'ilike', search)]
        return domain

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        SaleOrder = request.env['sale.order']
        quotation_count = SaleOrder.search_count(
            self._get_sale_quotation_domain())
        order_count = SaleOrder.search_count(
            self._get_sale_order_domain())
        values.update({
            'quotation_count': quotation_count,
            'order_count': order_count,
        })
        return values

    @http.route()
    def portal_my_orders(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        res = super(CustomerPortal, self).portal_my_orders(
            page, date_begin, date_end, sortby, **kw)
        search = kw.get('search', False)
        sale_domain = self._get_sale_order_domain(search)
        if date_begin and date_end:
            sale_domain += ([
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ])
        sale_obj = request.env['sale.order']
        order_count = sale_obj.search_count(sale_domain)
        sortby = res.qcontext['sortby']
        pager = portal_pager(
            url='/my/orders',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': res.qcontext['sortby'],
            },
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        sort_order = res.qcontext['searchbar_sortings'][sortby]['order']
        orders = sale_obj.search(
            sale_domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_orders_history'] = orders.ids[:100]
        res.qcontext.update({
            'orders': orders.sudo(),
            'pager': pager,
            'search': search
        })
        return res

    @http.route()
    def portal_order_page(
        self, order_id, report_type=None, access_token=None,
            message=False, download=False, **kw):
        res = super().portal_order_page(
            order_id=order_id, report_type=report_type, message=message,
            access_token=access_token, download=download, **kw)
        if report_type in ('html', 'pdf', 'text'):
            return res
        order = res.qcontext['sale_order']
        if not order.is_return:
            res.qcontext['return_orders'] = (
                request.env['sale.order'].sudo().search([
                    ('parent_sale_order', '=', order_id),
                    ('is_return', '=', True),
                    ('state', 'not in', ['cancel']),
                ])
            )
        return res

    def rma_form_validate(self, data, lines, order):
        errors = {}
        empty_order = True
        for i, line in enumerate(lines):
            val = data.get(str(line.id))
            notes = data.get('notes-%s' % str(line.id))
            try:
                val = int(val)
            except ValueError:
                errors.setdefault(i, {
                    'msg': (
                        _('Please provide integer numbers, not "%s"')
                        % val.upper()),
                    'product': line,
                })
                continue
            if val > 0:
                empty_order = False
                if not notes or notes == '':
                    errors.setdefault(i, {
                        'msg': (_('Reason for return is mandatory')),
                        'product': line,
                    })
            if val > line.product_uom_qty:
                errors.setdefault(i, {
                    'msg': (_('Return quantity exceeds the ordered')),
                    'product': line,
                })
            if val < 0:
                errors.setdefault(i, {
                    'msg': (_('The amount to be returned cannot be negative')),
                    'product': line,
                })
            return_lines = request.env['sale.order.line'].sudo().search(
                [('parent_sale_order_line', '=', line.id),
                 ('product_id', '=', line.product_id.id)])
            qty_returned = 0
            for return_line in return_lines:
                qty_returned += return_line.product_uom_qty
            if val > (line.product_uom_qty - qty_returned):
                errors.setdefault(i, {
                    'msg': (
                        _('Max quantity to return exceeded: %s,')
                        % int(line.product_uom_qty - qty_returned)),
                    'product': line,
                })
        if empty_order:
            errors.setdefault(-1, {
                'msg': (('You should select almost one product')),
                'product': None,
            })
        return errors

    @http.route(
        ['/my/orders/pdf/print-label/<int:order_id>'], type='http',
        auth='user', website=True)
    def print_address_label(self, order_id, access_token=None, **kw):
        order = self._document_check_access(
            'sale.order', order_id, access_token=access_token)
        pdf = request.env.ref(
            'website_rma.action_report_address_label').sudo().render_qweb_pdf(
            [order.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route([
        '/my/order/rma/<int:order>',
    ], type='http', auth='user', website=True)
    def portal_order_rma(self, order, access_token=None, **post):
        order = self._document_check_access(
            'sale.order', order, access_token=access_token)
        lines = []
        for order_line in order.order_line:
            product_id = order_line.product_id
            order_line_obj = request.env['sale.order.line']
            if product_id.type in order_line_obj._returnable_product_types() \
                    and order_line.product_id.is_returnable:
                lines.append(order_line)
        values = self._prepare_portal_layout_values()
        values.update({
            'errors': {},
            'order': order,
            'order_lines': lines,
            'page_name': 'new_rma',
        })
        if post:
            errors = self.rma_form_validate(post, lines, order)
            values['errors'] = errors
            values.update(post)
            if not errors:
                return_order = order.copy({
                    'is_return': True,
                    'order_line': False,
                    'parent_sale_order': order.id,
                    'website_id': False,
                })
                for order_line in lines:
                    qty_return = int(post[str(order_line.id)])
                    notes = post['notes-%s' % order_line.id]
                    if qty_return != 0:
                        order_line.qty_return = qty_return
                        order_line.copy({
                            'is_return': True,
                            'order_id': return_order.id,
                            'parent_sale_order_line': order_line.id,
                            'product_uom_qty': qty_return,
                            'notes': notes,
                        })
                values['return_order'] = return_order
                values['page_name'] = 'rma'
                template = request.env.ref('website_rma.email_template_rma')
                template.sudo().with_context(
                    lang=request.env.user.lang).send_mail(return_order.id)
                request.website.sale_reset()
                request.session.update({
                    'sale_last_order_id': False,
                })
                return request.render(
                    'website_rma.portal_return_order_page', values)
        return request.render('website_rma.portal_order_rma', values)
