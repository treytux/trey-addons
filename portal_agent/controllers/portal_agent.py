###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request

try:
    from odoo.addons.portal.controllers.portal import CustomerPortal
except ImportError:
    CustomerPortal = object


class PortalAgentCustomerPortal(CustomerPortal):
    def _get_agent_customers_domain(self, customer_id=None):
        partner_id = request.env.user.sudo().partner_id.id
        domain = [
            ('active', '=', True),
            ('customer', '=', True),
            ('agents', 'in', [partner_id]),
        ]
        if customer_id:
            domain = domain + [('id', '=', customer_id)]
        return domain

    def _get_agent_customer_orders_domain(self, customer_id):
        partner_id = request.env.user.sudo().partner_id.id
        return [
            ('agent', '=', partner_id),
            ('object_id.order_id.partner_id', '=', customer_id),
            ('object_id.order_id.state', 'in', ['sale', 'done']),
        ]

    def _prepare_portal_layout_values(self):
        res = super()._prepare_portal_layout_values()
        agent_customer_ids = request.env['res.partner'].sudo().search(
            self._get_agent_customers_domain(),
            order='name asc')
        res['agent_customers_count'] = len(agent_customer_ids)
        return res

    @http.route(['/my/customers'], type='http', auth='user', website=True)
    def portal_my_customers(self):
        agent_customers = request.env['res.partner'].sudo().search(
            self._get_agent_customers_domain())
        values = {
            'page_name': 'agent_customers',
            'agent_customers': agent_customers,
        }
        return request.render(
            'portal_agent.portal_my_customers', values)

    @http.route(
        ['/my/customer/<int:agent_customer_id>'], type='http', auth='user',
        website=True)
    def portal_my_customer(self, agent_customer_id):
        agent_customers = request.env['res.partner'].sudo().search(
            self._get_agent_customers_domain(customer_id=agent_customer_id))
        if not agent_customers:
            return request.redirect('/my/customers')
        agent_order_lines = request.env['sale.order.line.agent'].sudo().search(
            self._get_agent_customer_orders_domain(agent_customer_id))
        orders = agent_order_lines.mapped('object_id.order_id')
        values = {
            'page_name': 'agent_customer',
            'agent_customer': agent_customers[0],
            'agent_customer_orders_count': len(orders),
        }
        return request.render(
            'portal_agent.portal_my_customer', values)

    @http.route(
        ['/my/customer/orders/<int:agent_customer_id>'],
        type='http', auth='user', website=True)
    def portal_my_customer_orders(self, agent_customer_id):
        agent_order_lines = request.env['sale.order.line.agent'].sudo().search(
            self._get_agent_customer_orders_domain(agent_customer_id),
            order='id desc')
        orders = (
            agent_order_lines
            and agent_order_lines.mapped('object_id.order_id') or False)
        agent_customer = request.env['res.partner'].sudo().browse(
            agent_customer_id)
        values = {
            'page_name': 'agent_customer_orders',
            'agent_customer': agent_customer,
            'agent_customer_id': agent_customer_id,
            'orders': orders,
        }
        return request.render(
            'portal_agent.portal_my_customer_orders', values)

    @http.route(
        ['/my/customer/order/<int:order_id>'],
        type='http', auth='user', website=True)
    def portal_my_customer_order(self, order_id):
        order_sudo = request.env['sale.order'].browse(order_id).sudo()
        partner_id = request.env.user.sudo().partner_id.id
        if not any([
            line for line in order_sudo.order_line
                if partner_id in line.agents.mapped('agent.id')]):
            return request.render('website.404')
        values = {
            'sale_order': order_sudo,
            'message': False,
            'token': False,
            'return_url': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
        }
        return request.render('sale.sale_order_portal_template', values)

    @http.route(
        ['/my/customer/products/<int:agent_customer_id>'],
        type='http', auth='user', website=True)
    def portal_my_customer_products(self, agent_customer_id):
        agent_order_lines = request.env['sale.order.line.agent'].sudo().search(
            self._get_agent_customer_orders_domain(agent_customer_id))
        agent_customer = request.env['res.partner'].sudo().browse(
            agent_customer_id)
        values = {
            'page_name': 'agent_customer_products',
            'agent_customer': agent_customer,
            'products': {},
            'totals': {},
            'years': {},
        }
        if not agent_order_lines:
            return request.render(
                'portal_agent.portal_my_customer_products', values)
        dates = agent_order_lines.mapped('object_id.order_id.confirmation_date')
        min_year = min(dates).year
        max_year = max(dates).year
        years = {min_year + year for year in range(max_year - min_year + 1)}
        products = {}
        totals = {}
        for year in years:
            totals.setdefault(year, 0)
        for line in agent_order_lines:
            if not line.object_id.product_id.default_code:
                pass
            code = line.object_id.product_id.default_code
            order_year = line.object_id.order_id.confirmation_date.year
            products.setdefault(
                code,
                {
                    'name': '%s - %s' % (
                        line.object_id.product_id.default_code,
                        line.object_id.product_id.name),
                    'years': {},
                    'total': 0,
                }
            )
            for year in years:
                products[code]['years'].setdefault(year, 0)
            products[code]['years'][order_year] += int(line.object_id.product_uom_qty)
            products[code]['total'] += int(line.object_id.product_uom_qty)
            totals[order_year] += int(line.object_id.product_uom_qty)
        values.update({
            'products': [p[1] for p in sorted(products.items())],
            'years': years,
            'totals': totals,
        })
        return request.render(
            'portal_agent.portal_my_customer_products', values)

    def _get_sale_quotation_domain(self):
        partner_id = request.env.user.sudo().partner_id.commercial_partner_id.id
        return [
            ('message_partner_ids', 'child_of', [partner_id]),
            ('state', '=', 'sent')
        ]

    def _get_sale_order_domain(self):
        partner_id = request.env.user.sudo().partner_id.commercial_partner_id.id
        return [
            ('message_partner_ids', 'child_of', [partner_id]),
            ('state', 'in', ['sale', 'done'])
        ]
