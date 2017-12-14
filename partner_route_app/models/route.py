# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields, _
from datetime import datetime, date
import logging
_log = logging.getLogger(__name__)


class RouteApp(models.Model):
    _name = 'route.app'
    _description = 'Route App'

    @api.model
    def send_invoice_email(self, order_id):
        order = self.env['sale.order'].sudo().browse(order_id)
        if not order.invoice_ids:
            return {'error': 'Este pedido no tiene factura asociada'}
        if len(order.invoice_ids) > 1:
            return {'error': 'El pedido tiene mas de una factura, '
                             'no se puede enviar'}
        inv = order.invoice_ids[0]
        if inv.state not in ('draft', 'open', 'paid'):
            return {'error': 'La factura no se puede enviar, hable con '
                             'Administracion'}
        if inv.state == 'draft':
            inv.signal_workflow('invoice_open')

        template = self.env.ref('account.email_template_edi_invoice', False)
        email = template.sudo().generate_email(template.id, inv.id)
        if not inv.partner_id.email:
            email['partner_ids'] = [self.env.user.partner_id.id]
        ir_attach_obj = self.sudo().env['ir.attachment']
        for attach_fname, attach_datas in email.pop('attachments', []):
            data_attach = {
                'name': attach_fname,
                'datas': attach_datas,
                'datas_fname': attach_fname,
                'res_model': 'mail.compose.message',
                'res_id': 0,
                'type': 'binary',
            }
            email.setdefault('attachment_ids', list()).append(
                ir_attach_obj.create(data_attach).id)
        inv.with_context(mail_notify_force_send=False).message_post(**email)

        partners = self.env['res.partner'].browse(email['partner_ids'])
        emails = ', '.join([e.email for e in partners])
        return {'msg': 'Factura %s enviada a: %s' % (
            inv.number, emails)}

    @api.model
    def get_location(self, zipcode):
        locations = self.env['res.better.zip'].search(
            [('name', '=', zipcode)], limit=1)
        return {
            'id': locations and locations.id or None,
            'code': locations and locations.name or '',
            'city': locations and locations.city or '',
            'state': locations and locations.state_id.name or '',
            'state_id': locations and locations.state_id.id or None,
            'country': locations and locations.country_id.name or '',
            'country_id': locations and locations.country_id.id or None}

    @api.model
    def get_routes_partner(self, salesman_id=None):
        salesman_id = salesman_id or self.env.user.id
        routes = self.env['route'].search(
            [('user_id', '=', salesman_id)])
        return self._get_partners([r.id for r in routes])

    @api.model
    def get_routes(self, salesman_id=None):
        salesman_id = salesman_id or self.env.user.id
        routes = self.env['route'].search([('user_id', '=', salesman_id)])
        return [{
            'id': r.id,
            'name': r.name,
            'section_id': r.section_id.id,
            'section_name': r.section_id.name
        } for r in routes] if routes else []

    @api.model
    def _get_partners(self, route_ids):
        partners = self.env['res.partner'].search(
            [('route_id', 'in', route_ids)],
            order='pending_order desc, route_sequence asc')
        return [{
            'id': p.id,
            'name': p.name,
            'vat': p.vat,
            'display_name': p.display_name,
            'street': p.street,
            'zip': p.zip,
            'city': p.city,
            'state': p.state_id.name,
            'country': p.country_id.name,
            'phone': p.phone,
            'email': p.email,
            'image': p.image,
            'last_visit': p.last_visit,
            'last_visit_ago': p.last_visit_ago,
            'pending_order': p.pending_order,
            'route_sequence': p.route_sequence,
            'route_id': p.route_id.id,
            'route_name': p.route_id.name,
            'schedule': p.schedule if p.schedule else 'unspecified',
            'category_id': [{
                'id': c.id,
                'name': c.name,
                'complete_name': c.complete_name
            } for c in p.category_id]
        } for p in partners]

    @api.model
    def get_route(self, route_id):
        route = self.env['route'].browse(route_id)
        return {
            'id': route.id,
            'name': route.name,
            'zone': route.zone_id.name,
            'section': route.section_id.name,
            'partners': self._get_partners([route_id])
        }

    @api.model
    def get_visits(self, partner_id):
        visits = self.env['partner.visit'].sudo().search(
            [('partner_id', '=', partner_id)])
        return [{
            'id': v.id,
            'date': v.date,
            'order_id': v.order_id and v.order_id.id or None,
            'order_name': v.order_id and v.order_id.name or None,
            'order_state': v.order_id and v.order_id.state or None,
            'order_date_order': v.order_id and v.order_id.date_order or None,
            'order_amount_total':
                v.order_id and v.order_id.amount_total or None
        } for v in visits]
        # self.formatLang(str(datetime.today()), date_time=True)

    @api.model
    def get_stats(self):
        res = {
            'visits': 0,
            'orders': 0,
            'orders_amount_total': 0,
            'pending_orders': [],
        }

        today = fields.Datetime.to_string(
            datetime.combine(date.today(), datetime.min.time()))
        tomorrow = fields.Datetime.to_string(
            datetime.combine(date.today(), datetime.max.time()))
        # Visitas realizadas hoy
        visits = self.env['partner.visit'].sudo().search([
            ('user_id', '=', self.env.user.id),
            ('date', '>=', today),
            ('date', '<=', tomorrow)])
        if visits:
            res['visits'] = len(visits)

        # Pedidos realizados hoy
        orders = self.env['sale.order'].sudo().search([
            ('user_id', '=', self.env.user.id),
            ('date_order', '>=', today),
            ('date_order', '<=', tomorrow)])
        if orders:
            res['orders'] = len(orders)
            # Importe pedidos realizados hoy
            orders_amount_total = 0
            for o in orders:
                orders_amount_total = orders_amount_total + o.amount_total
            res['orders_amount_total'] = orders_amount_total

        # Clientes con pedidos pendientes de servir
        routes = self.env['route'].sudo().search([
            ('user_id', '=', self.env.user.id)])
        if routes:
            pending_orders = self.env['sale.order'].sudo().search([
                ('partner_id.route_id', 'in', routes.ids),
                ('state', 'in', ['draft', 'sent'])], order='date_order desc')
            if pending_orders:
                res['pending_orders'] = [{
                    'id': p.id,
                    'name': p.name,
                    'partner': {
                        'id': p.partner_id.id,
                        'name': p.partner_id.name,
                        'vat': p.partner_id.vat,
                        'display_name': p.partner_id.display_name,
                        'street': p.partner_id.street,
                        'zip': p.partner_id.zip,
                        'city': p.partner_id.city,
                        'state': p.partner_id.state_id.name,
                        'country': p.partner_id.country_id.name,
                        'phone': p.partner_id.phone,
                        'email': p.partner_id.email,
                        'image': p.partner_id.image,
                        'last_visit': p.partner_id.last_visit,
                        'last_visit_ago': p.partner_id.last_visit_ago,
                        'pending_order': p.partner_id.pending_order,
                        'route_sequence': p.partner_id.route_sequence,
                        'schedule': p.partner_id.schedule or 'unspecified',
                        'category_id': [{
                            'id': c.id,
                            'name': c.name,
                            'complete_name': c.complete_name
                        } for c in p.partner_id.category_id]
                    },
                    'date': p.date_order,
                    'route': {
                        'id': p.partner_id.route_id.id,
                        'name': p.partner_id.route_id.name,
                    }
                } for p in pending_orders]

        return res

    @api.model
    def get_partner_stats(self, partner_id):
        res = {
            'last_visit': False,
            'last_visit_ago': False,
            'time_between_visits': False,
            'pending_orders': False,
            'latest_products': False,
            'latest_gifts': False,
            'latest_stocks': False}
        visits = self.env['partner.visit'].sudo().search(
            [('partner_id', '=', partner_id)], order='date desc')
        if not visits:
            return res
        first_element = visits[0]
        last_element = visits[-1:]
        d1 = fields.Datetime.from_string(first_element.date)
        d2 = fields.Datetime.from_string(last_element.date)
        res.update({
            'last_visit': first_element.partner_id.last_visit,
            'last_visit_ago': first_element.partner_id.last_visit_ago,
            'time_between_visits': (d1 - d2).days / len(visits)})
        sale_orders = self.env['sale.order'].sudo().search([
            ('partner_id', '=', partner_id),
            ('state', 'in', ['draft', 'sent'])])
        if sale_orders:
            lines = [l for o in sale_orders for l in o.order_line]
            gr_products = {'%s:%s' % (l.product_id.id, l.product_uom.id): {
                'id': l.product_id.id,
                'name': ' '.join((
                    [l.product_id.name] +
                    [a.name for a in l.product_id.attribute_value_ids])),
                'qty': 0,
                'uom': l.product_uom.name,
                'image': l.product_id.image_small} for l in lines}
            for l in lines:
                key = '%s:%s' % (l.product_id.id, l.product_uom.id)
                gr_products[key]['qty'] += l.product_uom_qty
            res['pending_products'] = gr_products.values()

        last_ordered = self.env['partner.visit'].sudo().search(
            [('partner_id', '=', partner_id),
             ('order_id', '!=', False)],
            order='date desc', limit=1)
        if last_ordered:
            lines = [l for o in last_ordered for l in o.order_id.order_line]
            gr_products = {'%s:%s' % (l.product_id.id, l.product_uom.id): {
                'id': l.product_id.id,
                'name': ' '.join((
                    [l.product_id.name] +
                    [a.name for a in l.product_id.attribute_value_ids])),
                'qty': 0,
                'uom': l.product_uom.name,
                'image': l.product_id.image_small} for l in lines}
            for l in lines:
                key = '%s:%s' % (l.product_id.id, l.product_uom.id)
                gr_products[key]['qty'] += l.product_uom_qty
            res['latest_products'] = gr_products.values()

            lines = [l for o in last_ordered for l in o.order_id.gift_ids]
            gr_gifts = {'%s:%s' % (l.product_id.id, l.uom_id.id): {
                'id': l.product_id.id,
                'name': ' '.join((
                    [l.product_id.name] +
                    [a.name for a in l.product_id.attribute_value_ids])),
                'qty': l.quantity,
                'uom': l.uom_id.name,
                'image': l.product_id.image_small} for l in lines}
            res['latest_gifts'] = gr_gifts.values()

        last_stocked = self.env['partner.visit'].sudo().search(
            [('partner_id', '=', partner_id),
             ('stock_ids', '!=', False)],
            order='date desc', limit=1)
        if not last_stocked:
            return res
        res['latest_stocks'] = [{
            'id': s.product_id.id,
            'name': ' '.join((
                [s.product_id.name] +
                [a.name for a in s.product_id.attribute_value_ids])),
            'qty': s.qty,
            'uom': s.uom_id.name,
            'image': s.product_id.image_small
        } for s in last_stocked.stock_ids]

        return res


class Visit(models.Model):
    _inherit = 'partner.visit'

    @api.model
    def create_partner_visit(self, visit_data, stock_lines=[]):
        '''Create a partner visit with data dictionary given as a parameter.'''
        if 'route_id' not in visit_data:
            _log.warning(_('Field route_id is required!'))
            return None
        elif 'user_id' not in visit_data:
            _log.warning(_('Field user_id is required!'))
            return None
        elif 'partner_id' not in visit_data:
            _log.warning(_('Field partner_id is required!'))
            return None

        visit = self.env['partner.visit'].create(visit_data)
        for stock in stock_lines:
            if not stock['qty']:
                continue
            self.env['partner.visit.stock'].create({
                'visit_id': visit.id,
                'product_id': stock['product_id'],
                'qty': stock['qty']})

        return visit.id
