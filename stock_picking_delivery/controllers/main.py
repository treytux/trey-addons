# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
from openerp.http import request
import werkzeug.utils as utils


class StockPickingDelivery(http.Controller):
    @http.route(
        '/stock-picking-delivery/ok/<token>', auth='public', type='http',
        website=True)
    def accept_delivery(self, token):
        delivery_obj = request.env['stock.picking.delivery']
        delivery = delivery_obj.sudo().search([('token', '=', token)])
        if not delivery:
            return request.render('website.404')
        delivery.sudo().to_accepted()
        return request.render(
            'stock_picking_delivery.stock_picking_delivery_sended_layout', {
                'delivery': delivery, 'action': 'ok'})

    @http.route(
        '/stock-picking-delivery/ko/<token>', auth='public', type='http',
        website=True)
    def not_accept_delivery(self, token):
        delivery_obj = request.env['stock.picking.delivery']
        delivery = delivery_obj.sudo().search([('token', '=', token)])
        if not delivery:
            return request.render('website.404')
        return request.render(
            'stock_picking_delivery.stock_picking_delivery_layout', {
                'token': token})

    @http.route(
        '/not-accept-delivery-reasons/', auth='public', type='http',
        website=True)
    def not_accept_delivery_reasons(self, **post):
        if not post:
            return utils.redirect('/')
        delivery_obj = request.env['stock.picking.delivery']
        delivery = delivery_obj.sudo().search(
            [('token', '=', post['access_token'])])
        if not delivery:
            return request.render('website.404')
        if delivery.delivery_contact_id.user_ids:
            delivery.env.uid = delivery.delivery_contact_id.user_ids[0].id
        msg = delivery.with_context(mail_post_autofollow=False).message_post(
            body=post['reason'], subject='Delivery refused')
        if post.get('attachment'):
            files = request.httprequest.files.getlist('attachment')
            attachemnts = []
            for file in files:
                data = file.read()
                attach = request.env['ir.attachment'].sudo().create({
                    'res_model': 'mail.message',
                    'res_id': msg,
                    'datas_fname': file.filename,
                    'datas': data.encode('base64'),
                    'name': file.filename})
                attachemnts.append(attach.id)
            message = request.env['mail.message'].sudo().browse(msg)
            message.attachment_ids = attachemnts
        delivery.sudo().to_not_accepted()
        return request.render(
            'stock_picking_delivery.'
            'stock_picking_delivery_sended_layout', {
                'delivery': delivery, 'action': 'ko'})
