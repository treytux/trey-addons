###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.addons import decimal_precision as dp


class ProductStandardPriceHistory(models.Model):
    _inherit = 'product.standard_price.history'

    market_cost = fields.Float(
        string='Market cost',
        group_operator='avg',
        digits=dp.get_precision('Product Price'),
    )
    team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Team',
    )
