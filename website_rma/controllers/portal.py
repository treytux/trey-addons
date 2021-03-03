###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, http
from odoo.addons.portal.controllers.portal import pager
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.http import request


class CustomerPortal(CustomerPortal):
    def _get_domain(self, commercial_id):
        return [
            ('message_partner_ids', 'child_of', commercial_id),
            ('state', 'in', ['sale', 'done']),
            ('is_return', '=', False)]

    def _label_check_access(self, order_id):
        partner_id = request.env.user.partner_id.commercial_partner_id.id
        order_sudo = request.env['sale.order'].sudo().search([
            ('id', '=', order_id),
            ('partner_id', '=', partner_id),
        ], limit=1)
        return order_sudo

    @http.route()
    def portal_order_page(self, order=None, access_token=None, **kw):
        res = super().portal_order_page(order, access_token=access_token, **kw)
        order_sudo = request.env['sale.order'].sudo().browse([order])
        if not order_sudo.is_return:
            return_orders = request.env['sale.order'].sudo().search(
                [('parent_sale_order', '=', order_sudo.id),
                 ('is_return', '=', True)])
            res.qcontext['return_orders'] = return_orders
            return res
        res.qcontext['order'] = order_sudo
        return request.render(
            'website_rma.portal_return_order_page', res.qcontext)

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        sale_order = request.env['sale.order']
        commercial_id = request.env.user.partner_id.commercial_partner_id.id
        order_count = sale_order.search_count(self._get_domain(commercial_id))
        values.update({'order_count': order_count})
        return values

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
                        _("Please provide integer numbers, not '%s'")
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
                        _("Max quantity to return exceeded: %s,")
                        % int(line.product_uom_qty - qty_returned)),
                    'product': line,
                })
        if empty_order:
            errors.setdefault(-1, {
                'msg': (("You should select almost one product")),
                'product': None,
            })
        return errors

    @http.route(
        ['/my/orders/pdf/print-label/<int:order_id>'], type='http',
        auth="user", website=True)
    def print_address_label(self, order_id, access_token=None, **kw):
        order_sudo = self._label_check_access(order_id)
        if not order_sudo:
            return request.redirect('/my')
        pdf = request.env.ref(
            'website_rma.action_report_address_label').sudo().render_qweb_pdf(
            [order_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route([
        '/my/order/rma/<int:order>',
    ], type='http', auth='user', website=True)
    def portal_order_rma(self, order, access_token=None, **post):
        order_sudo = self._order_check_access(order, access_token=access_token)
        lines = []
        for order_line in order_sudo.order_line:
            if (
                order_line.product_id.type == 'product' and
                    order_line.is_returnable and
                    order_line.product_id.is_returnable):
                lines.append(order_line)
        values = self._prepare_portal_layout_values()
        values.update({
            'errors': {},
            'order': order_sudo,
            'order_lines': lines,
            'page_name': 'rma',
        })
        if not len(lines):
            values['errors'].setdefault(-1, {
                'msg': (_("There are no products compatible with return")),
                'product': None,
            })
            return request.render('website_rma.portal_order_rma', values)
        if post:
            errors = self.rma_form_validate(post, lines, order_sudo)
            values['errors'] = errors
            values.update(post)
            if not errors:
                return_order = order_sudo.copy({
                    'is_return': True,
                    'order_line': False,
                    'parent_sale_order': order_sudo.id,
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
                values['order'] = return_order
                template = request.env.ref('website_rma.email_template_rma')
                template.sudo().with_context(
                    lang=request.env.user.lang).send_mail(return_order.id)
                return request.render(
                    'website_rma.portal_return_order_page', values)
        return request.render('website_rma.portal_order_rma', values)

    @http.route()
    def portal_my_orders(self, page=1, date_begin=None, date_end=None,
                         sortby=None, **kw):
        res = super().portal_my_orders(
            page, date_begin, date_end, sortby, **kw)
        sale_obj = request.env['sale.order']
        commercial_id = request.env.user.partner_id.commercial_partner_id.id
        sale_domain = self._get_domain(commercial_id)
        res.qcontext['order_count'] = sale_obj.search_count(sale_domain)
        res.qcontext['pager'] = pager(
            url='/my/orders',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby},
            total=res.qcontext['order_count'],
            page=page,
            step=self._items_per_page
        )
        offset = res.qcontext['pager']['offset']
        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']
        res.qcontext['orders'] = sale_obj.search(
            sale_domain, order=sort_order, limit=self._items_per_page,
            offset=offset)
        return res
