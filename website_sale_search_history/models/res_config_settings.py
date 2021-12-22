###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    search_history_term_length = fields.Integer(
        string='Search term length',
        help='Minimun length of relevant terms in searches. Terms of less '
             'length will be ignored.',
        related='website_id.search_history_term_length',
        readonly=False,
    )
    search_history_store = fields.Selection(
        string='Store searches',
        help='Indicates if the search is always saved or only if it does not '
             'find results.',
        related='website_id.search_history_store',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        term_length = int(config_parameter.get_param(
            'website.search_history_term_length'))
        store = config_parameter.get_param('website.search_history_store')
        res.update(
            search_history_term_length=term_length,
            search_history_store=store,
        )
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param(
            'website.search_history_term_length',
            self.search_history_term_length)
        set_param('website.search_history_store', self.search_history_store)
