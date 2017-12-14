# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
from openerp.http import request


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _signup_create_user(self, values):
        user_id = super(ResUsers, self)._signup_create_user(values)
        if user_id:
            env = request.env
            user = env['res.users'].sudo().search([('id', '=', int(user_id))])
            config_param = self.env['ir.config_parameter']
            template_user_id = config_param.get_param(
                'auth_signup.template_user_id')
            template_user = env['res.users'].sudo().search(
                [('id', '=', int(template_user_id)), ('active', '=', False)])
            if template_user:
                partner_id = template_user.partner_id
                user.write({
                    'is_company': (
                        partner_id.is_company and
                        partner_id.is_company or None),
                    'user_id': (
                        partner_id.user_id and
                        partner_id.user_id.id or None),
                    'property_account_position': (
                        partner_id.property_account_position and
                        partner_id.property_account_position.id or None),
                    'vat_subjected': (
                        partner_id.vat_subjected and
                        partner_id.vat_subjected or None),
                    'property_account_receivable': (
                        partner_id.property_account_receivable and
                        partner_id.property_account_receivable.id or None),
                    'property_account_payable': (
                        partner_id.property_account_payable and
                        partner_id.property_account_payable.id or None),
                    'property_payment_term': (
                        partner_id.property_payment_term and
                        partner_id.property_payment_term.id or None),
                    'property_supplier_payment_term': (
                        partner_id.property_supplier_payment_term and
                        partner_id.property_supplier_payment_term.id or None)})
        return user_id
