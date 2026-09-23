###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _get_sale_line_domain(self):
        user_catalog_ids = self.env.user.catalog_ids.ids
        domain = [('sale_ok', '=', True)]
        if user_catalog_ids:
            domain.extend([
                '|',
                ('catalog_ids', '=', False),
                ('catalog_ids', 'in', user_catalog_ids),
            ])
        return domain

    product_id = fields.Many2one(
        domain=_get_sale_line_domain,
    )
