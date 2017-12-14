# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _get_signup_url_for_action(self, action=None, view_type=None,
                                   menu_id=None, res_id=None, model=None):
        res = super(ResPartner, self)._get_signup_url_for_action(
            action=action, view_type=view_type, menu_id=menu_id,
            res_id=res_id, model=model)
        auth_url = self.env['ir.config_parameter'].get_param('auth_signup.url')
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        for url in res:
            res[url] = res[url].replace(base_url, auth_url)
        return res
