# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class StockConfigSettings(models.TransientModel):
    _inherit = 'stock.config.settings'

    users_to_send_exception_ids = fields.Many2many(
        comodel_name='res.users',
        relation='res_company_user_send_excep_rel',
        column1='company_id',
        column2='user_id',
        help='Users who will be informed by mail of procurement in exception '
             'state.',
    )

    @api.model
    def get_default_values(self, fields):
        user_ids = self.env['ir.config_parameter'].sudo().get_param(
            'procurement_send_exception_errors.users_to_send_exception_ids')
        return {
            'users_to_send_exception_ids': [
                (6, 0, user_ids and eval(user_ids) or [])]}

    @api.multi
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'procurement_send_exception_errors.users_to_send_exception_ids',
            self.users_to_send_exception_ids.ids)
