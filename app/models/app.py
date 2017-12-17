# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields, _
import json
import logging
_log = logging.getLogger(__name__)


class App(models.AbstractModel):
    _name = 'app'
    _description = 'App'

    @api.model
    def get_stock_location(self):
        partner = self.env.user.partner_id
        location = self.env['stock.location'].sudo().search(
            [('partner_id', '=', partner.id),
                ('active', '=', 1)], limit=1)
        if location:
            products = self.env['product.product'].with_context({
                'location': location.id}).sudo().search(
                    [('location_id', '=', location.id)],
                    order='name asc')
            return {
                'id': location and location.id or None,
                'code': location and location.name or '',
                'products': [{
                    'id': p.id,
                    'name': p.name,
                    'qty_available': p.qty_available,
                    'uom_name': p.uom_id.name,
                    'image': p.image_small
                } for p in products] if products else []}
        else:
            return False

    @api.model
    def get_order_totals(self, partner_id, lines):
        partner = self.env['res.partner'].browse(partner_id)
        pricelist = partner.property_product_pricelist
        fiscal_id = self.env['account.fiscal.position'].get_fiscal_position(
            self.env.user.company_id.id, partner_id)
        res = {'lines': []}
        for line in lines:
            if not line['price_unit']:
                continue
            ln = self.env['sale.order.line'].product_id_change(
                pricelist.id, line['product_id'], qty=line['qty'],
                uom=line['uom_id'], qty_uos=0, uos=False,
                name='', partner_id=partner_id, lang=False, update_tax=True,
                date_order=False, packaging=False, fiscal_position=fiscal_id,
                flag=False, context=None)
            ln = ln['value']

            tax = self.env['account.tax'].browse(ln['tax_id'])
            v = tax.compute_all(ln['price_unit'], ln['product_uom_qty'],
                                line['product_id'], partner_id)
            ln['tax_total'] = v['total_included'] - v['total']
            ln['tax_total_included'] = v['total_included']
            ln['tax'] = v
            res['lines'].append(ln)
        return res

    @api.model
    def create_visit(self, route_id, partner_id, lines, stocks, notes=''):
        visit = self.env['partner.visit'].create({
            'route_id': route_id,
            'user_id': self.env.user.id,
            'date': fields.Datetime.now(),
            'partner_id': partner_id,
            'notes': notes
            # 'order_id': ,
            # 'stock_ids': ,
        })
        for stock in stocks:
            product = self.env['product.product'].browse(stock['product_id'])
            self.env['partner.visit.stock'].sudo().create({
                'visit_id': visit.id,
                'product_id': stock['product_id'],
                'qty': stock['qty'],
                'uom_id': product.uom_id.id
            })

        if not lines:
            return {'visit_id': visit.id, 'order_id': None}

        loc_id = self.env.user.current_vehicle_id.stock_location_id
        warehouse = loc_id.get_warehouse(loc_id)
        order = self.env['sale.order'].create({
            'partner_id': visit.partner_id.id,
            'partner_invoice_id': visit.partner_id.id,
            'partner_shipping_id': visit.partner_id.id,
            'user_id': self.env.user.id,
            'pricelist_id': (
                visit.partner_id.property_product_pricelist and
                visit.partner_id.property_product_pricelist.id or None),
            'order_policy': 'manual',
            'warehouse_id': warehouse})
        fiscal_position = order.partner_id.property_account_position or None
        gifts_sended = []
        for line in lines:
            if 'promotion_line_ids' in line:
                gifts_sended.append(line)
                continue
            product = self.env['product.product'].browse(line['product_id'])
            tax_ids = product.product_tmpl_id.taxes_id
            taxs = (fiscal_position and
                    fiscal_position.map_tax(tax_ids) or tax_ids)
            self.env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': product.id,
                'product_uom_qty': line['qty'],
                'product_uom': line['uom_id'],
                # @todo El precio lo tiene que marca el pedio,
                # no hacer caso de lo que viene
                'price_unit': line['price_unit'],
                'name': product.name,
                'tax_id': [(6, 0, [t.id for t in taxs])],
                'state': 'draft',
            })
        order.update_gifts()
        for gift in order.gift_ids:
            lines = sum([g['qty'] for g in gifts_sended
                         if (g['product_id'] == gift.product_id.id and
                             g['uom_id'] == gift.uom_id.id)])
            gift.quantity = lines
        # Confirmar pedido
        order.action_button_confirm()

        # Confirmar albaran
        for pick in order.picking_ids:
            for line in pick.move_lines:
                # Cambiar la ubicacion de salida
                line.location_id = loc_id
            pick.action_assign()
            if pick.state in ['confirmed', 'waiting', 'partially_available']:
                pick.force_assign()
            pick.do_transfer()
            pick.action_confirm()

        # Crear factura
        order.action_invoice_create()

        # Cancelar pedidos pendientes
        pendings = self.env['sale.order'].search([
            ('partner_id', '=', partner_id),
            ('state', 'in', ['draft', 'sent'])])
        for pending in pendings:
            pending.action_cancel()
            subject = _('Pedido cancelado por visita del comercial')
            body = _(
                'Se cancela el pedido por visita registrada del '
                'comercial %s (%s)' % (
                    self.env.user.name,
                    self.env.user.login))
            pending.with_context(mail_post_autofollow=False).message_post(
                body=body, subject=subject, type='notification')
            pending.visit_id = visit.id

        visit.order_id = order.id
        return {'visit_id': visit.id, 'order_id': visit.order_id.id}

    @api.model
    def create_picking(self, location_src_id, location_dst_id, lines):
        loc_id = self.env['stock.location'].browse(location_src_id)
        warehouse_id = loc_id.get_warehouse(loc_id)
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('warehouse_id', '=', warehouse_id)])[:1]

        pick = self.env['stock.picking'].create({
            'origin': 'Mobile App',
            'notes': json.dumps(lines),
            'move_type': 'one',
            'date': fields.Datetime.now(),
            'date_done': fields.Datetime.now(),
            'partner_id': self.env.user.partner_id.id,
            'company_id': self.env.user.company_id.id,
            'picking_type_id': picking_type.id,
            'location_id': location_src_id,
            'location_dest_id': location_dst_id})
        for line in lines:
            product = self.env['product.product'].browse(
                int(line['product_id']))
            data = {
                'picking_id': pick.id,
                'name': product.name,
                'partner_id': self.env.user.partner_id.id,
                'create_date': fields.Datetime.now(),
                'product_id': product.id,
                'location_id': location_src_id,
                'location_dest_id': location_dst_id,
                'origin': 'Mobile App',
                'product_uom': line['uom_id'],
                'product_uom_qty': line['qty']}
            self.env['stock.move'].create(data)
        pick.force_assign()
        pick.action_confirm()
        pick.action_done()
        return self._return_picking(pick)

    @api.model
    def get_stock_locations(self):
        partner = self.env.user.partner_id
        locations = self.env['stock.location'].search(
            [('partner_id', '=', partner.id)], limit=1)
        return [{
            'id': l.id,
            'name': l.name}
            for l in locations]

    @api.model
    def get_products(self):
        uom_categ = {}
        for uom in self.env['product.uom'].search([]):
            uom_categ.setdefault(uom.category_id.id, []).append({
                'id': uom.id,
                'name': uom.name,
                'type': uom.uom_type,
                'factor': round(uom.factor_inv, 2)})

        location_ids = [l['id'] for l in self.get_stock_locations()]
        ctx = dict(self.env.context)
        ctx.update({'location': location_ids})
        products = self.env['product.product'].with_context(ctx).search(
            [('sale_ok', '=', True)], order='name asc')
        return [{
            'id': p.id,
            'name': p.name,
            'attributes': [a.name for a in p.attribute_value_ids],
            'qty_available': p.qty_available,
            'uom': {
                'id': p.uom_id.id,
                'name': p.uom_id.name,
                'category_id': p.uom_id.category_id.id,
                'category_name': p.uom_id.category_id.name,
                'type': p.uom_id.uom_type,
                'factor': round(p.uom_id.factor_inv, 2)},
            'uom_categ': (
                p.uom_id.category_id.id in uom_categ and
                sorted(uom_categ[p.uom_id.category_id.id],
                       key=lambda e: e['factor']) or []),
            'image': p.image_small}
            for p in products]

    @api.model
    def get_products_prices(self, partner_id, products):
        partner = self.env['res.partner'].browse(partner_id)
        pricelist = partner.priceslist_id
        pricelist.get_prices()

        promo_lines = self.get_promolines()
        self._apply_promotion_price(promo_lines)
        self._apply_promotion_gifts(promo_lines)

    def _return_picking(self, picking):
        return {
            'id': picking.id,
            'name': picking.name,
            'date': picking.date,
            'state': picking.state,
            'partner': {
                'id': picking.partner_id.id,
                'name': picking.partner_id.name},
            'lines': [{
                'id': line.id,
                'product': {
                    'id': line.product_id.id,
                    'name': line.product_id.name},
                'uom_id': line.product_uom.id,
                'uom_name': line.product_uom.name,
                'qty': line.product_uom_qty}
                for line in picking.move_lines],
            'qty': sum([line.product_uom_qty for line in picking.move_lines])}

    @api.model
    def get_pickings(self, domain=None):
        if domain is None:
            domain = []
        if 'state' not in domain:
            domain.append(['state', '=', 'done'])

        pickings = self.env['stock.picking'].sudo().search(
            domain, order='date desc')
        return [self._return_picking(p) for p in pickings]

    @api.model
    def get_picking(self, picking_id):
        return self._return_picking(
            self.env['stock.picking'].browse(picking_id))

    @api.model
    def get_orders(self):
        sale_orders = self.env['sale.order'].search([])
        return [{
            'id': so.id,
            'name': so.name,
            'state': so.state,
            'date_order': so.date_order,
            'amount_total': so.amount_total
        } for so in sale_orders]

    @api.model
    def get_order(self, order_id):
        order = self.env['sale.order'].sudo().browse(order_id)
        return {
            'id': order.id,
            'name': order.name,
            'partner_id': order.partner_id.id,
            'amount_untaxed': order.amount_untaxed,
            'amount_tax': order.amount_tax,
            'amount_total': order.amount_total,
            'order_line': [{
                'id': l.id,
                'product_id': l.product_id.id,
                'product_name': l.product_id.name,
                'uom_id': l.product_uom.id,
                'uom_name': l.product_uom.name,
                'qty': l.product_uom_qty,
                'price_unit': l.price_unit,
                'discount': l.discount,
                'price_subtotal': l.price_subtotal,
            } for l in order.order_line]
        }

    @api.model
    def get_locations(self, country_ids=None):
        '''Get the locations aka better zips of countries given as a
         parameter. If the list of countries is empty, it returns locations
         from countries with Published in App option marked as True.'''
        locations = []
        if not country_ids:
            countries = self.env['res.country'].search_read(
                [('app_published', '=', True)], ['id', 'name'])
            country_ids = []
            if countries:
                for c in countries:
                    country_ids.append(c['id'])
        if country_ids:
            published_locations = self.env['res.better.zip'].search([
                ('country_id', 'in', country_ids)], order='name asc')
            if published_locations:
                for c in published_locations:
                    locations.append({
                        'id': c.id,
                        'zip': c.name,
                        'city': c.city,
                        'state_id': c.state_id.id,
                        'state_name': c.state_id.name,
                        'country_id': c.country_id.id})
        return locations

    @api.model
    def get_location_by_zip(self, search_zip):
        domain = [('name', 'ilike', search_zip)]
        country_id = self.env.user.company_id.country_id.id
        if country_id:
            domain.append(('country_id', '=', country_id))
        locations = self.env['res.better.zip'].search(domain, order='name asc')
        return (search_zip, [{
            'id': l.id,
            'zip': l.name,
            'city': l.city,
            'state_id': l.state_id.id,
            'state_name': l.state_id.name,
            'country_id': l.country_id.id,
            'country_name': l.country_id.name,
        } for l in locations])

    @api.model
    def get_states(self, country_ids=None):
        '''Get the states of countries given as a parameter.
         If the list of countries is empty, it returns states from countries
         with Published in App option marked as True.'''
        states = []
        if not country_ids:
            countries = self.env['res.country'].search_read(
                [('app_published', '=', True)], ['id', 'name'])
            country_ids = []
            if countries:
                for c in countries:
                    country_ids.append(c['id'])
        if country_ids:
            published_states = self.env['res.country.state'].search([
                ('country_id', 'in', country_ids)], order='name asc')
            if published_states:
                for s in published_states:
                    states.append({
                        'id': s.id,
                        'name': s.name,
                        'country_id': s.country_id.id,
                    })
        return states

    @api.model
    def get_countries(self):
        '''Returns a list with all countries that have active the published app
        field.'''
        countries = self.env['res.country'].search(
            [('app_published', '=', True)], order='name asc')
        return [{
            'id': c.id,
            'name': c.name,
            'code': c.code
        } for c in countries] if countries else []

    @api.model
    def get_mail_messages(self, domain=None):
        if domain is None:
            domain = []
        mail_messages = self.env['mail.message'].search(
            domain, order='date desc')
        return [{
            'id': m.id,
            'author': {
                'id': m.author_id.id,
                'name': m.author_id.name,
            },
            'subject': m.subject,
            'body': m.body,
            'date': m.date,
        } for m in mail_messages] if mail_messages else []

    @api.model
    def send_email(self, email_from, email_to, subject,
                   body_html, attachment_ids=None):
        mail_mail = self.env['mail.mail']
        mail_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
            'type': 'email',
        }

        try:
            if len(attachment_ids) > 0:
                mail_values['attachment_ids'] = [
                    (0, 0, a) for a in attachment_ids]
            mail = mail_mail.create(mail_values)
        except Exception:
            return {'errors': [
                {'name': 'Creación email',
                 'value': 'Error al crear email y/o adjuntos'}]}
        try:
            mail.send()
            return True
        except Exception:
            return {'errors': [
                {'name': 'Envío email', 'value': 'Error al enviar email'}]}
