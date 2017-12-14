# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
import logging

_log = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _signup_create_user(self, values):
        user_id = super(ResUsers, self)._signup_create_user(values)
        config_param = self.env['ir.config_parameter']
        res_users_obj = self.env['res.users']
        template_user_id = config_param.get_param(
            'auth_signup.template_user_id')
        user = res_users_obj.browse(user_id)
        template_user = res_users_obj.browse(int(template_user_id))
        user.write(
            {'property_account_position': (
                template_user.partner_id.property_account_position and
                template_user.partner_id.property_account_position.id or
                None)})
        return user_id
