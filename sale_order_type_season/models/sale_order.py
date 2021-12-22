###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_season = fields.Boolean(
        string='Is season',
    )

    def onchange_type_id(self):
        res = super().onchange_type_id()
        for order in self:
            if order.type_id.is_season:
                order.update({
                    'is_season': True,
                })
        return res
