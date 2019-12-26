# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    users_to_inform_ids = fields.Many2many(
        comodel_name='res.users',
        string='Users whose will be informed of their the blocked partners')

    @api.model
    def get_default_values(self, fields):
        user_ids = self.env['ir.config_parameter'].sudo().get_param(
            'account_partner_debt_blocking.users_to_inform_ids')
        return {
            'users_to_inform_ids': [(6, 0, user_ids and eval(user_ids) or [])]}

    @api.multi
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'account_partner_debt_blocking.users_to_inform_ids',
            self.users_to_inform_ids.ids)
