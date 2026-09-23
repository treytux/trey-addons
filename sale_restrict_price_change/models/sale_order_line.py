###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('price_unit')
    def onchange_price_unit(self):
        if self.product_id and 'pricelist' not in self.env.context \
                and not self.env.user.has_group(
                    'sale_restrict_price_change.group_allow_change_price'):
            raise UserError(_(
                'You do not have permissions to change the price.'))
