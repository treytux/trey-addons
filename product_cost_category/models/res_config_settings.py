###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cost_category_price_setting = fields.Selection(
        string='Cost Category Price Update',
        selection=[
            ('manual', 'Manual '),
            ('automatic', 'Automatic')
        ],
        default='manual',
        config_parameter='product_cost_category.cost_category_price_setting',
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter']
        cost_category_price_setting = param_obj.get_param(
            'product_cost_category.cost_category_price_setting')
        res.update(cost_category_price_setting=cost_category_price_setting)
        return res
