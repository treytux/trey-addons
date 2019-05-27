# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http, _
from openerp.http import request
import openerp.addons.website_sale.controllers.main as main


class WebsiteSale(main.website_sale):
    @http.route(['/shop/payment/discount'],
                type='json', auth='user', methods=['post'], website=True)
    def payment_method_discount(self, action, acquirer):
        acquirer = request.env['payment.acquirer'].browse(int(acquirer))
        order_id = request.session.get('sale_order_id')
        if not acquirer or not order_id:
            return
        order = request.env['sale.order'].browse(order_id)
        user = request.env['res.users'].browse(request.uid)
        if user.partner_id != order.partner_id:
            return
        if action == 'discount':
            if order.website_sale_acquire_discount_applied:
                self.delete_payment_discount(acquirer, order)
                self.create_payment_discount(acquirer, order)
                return 'Discount applied'
            else:
                self.create_payment_discount(acquirer, order)
                return 'Discount applied'
        elif action == 'delete_discount':
            self.delete_payment_discount(acquirer, order)
            return 'Discount deleted'
        else:
            return 'Exception error'

    def create_payment_discount(self, acquirer, order):
        data = {'discount_type': acquirer.discount_type,
                'product_id': acquirer.product_id.id,
                'discount_display_name': _('Payment method discount')}
        if acquirer.discount_type == 'percent_total':
            data.update({'discount_applied': acquirer.discount_applied})
        elif acquirer.discount_type == 'quantity_total':
            data.update({'discount_quantity': acquirer.discount_quantity})
        prod = request.env['product.product'].sudo().browse(
            acquirer.product_id.id)
        taxes = order.fiscal_position.sudo().map_tax(prod.taxes_id)
        data.update({'discount_taxes': [(6, 0, taxes.ids)]})
        wiz = request.env['wiz.sale.discount'].with_context({
            'active_ids': [order.id],
            'active_model': 'sale.order',
            'active_id': order.id}).create(data)
        try:
            wiz.sudo().button_accept()
        except Exception as e:
            if 'can not greater than sale order amount total' in e.message:
                return 'Discount greater than the amount of the order'
        order.sudo().write({'payment_mode_id': acquirer.payment_mode_id.id,
                            'payment_acquirer_id': acquirer.id,
                            'website_sale_acquire_discount_applied': True})
        order.button_dummy()

    def delete_payment_discount(self, acquirer, order):
        payment_acquirers = request.env['payment.acquirer'].search([
            ('website_published', '=', True)])
        discount_product_ids = [
            product.id for payment_ac in payment_acquirers
            for product in payment_ac.product_id]
        order_line_with_discount = list(set(order.order_line.filtered(
            lambda line: line.product_id.id in discount_product_ids)))
        [line.sudo().unlink() for line in order_line_with_discount]
        order.sudo().write({'website_sale_acquire_discount_applied': False,
                            'payment_mode_id': acquirer.payment_mode_id.id,
                            'payment_acquirer_id': acquirer.id})
        order.button_dummy()
