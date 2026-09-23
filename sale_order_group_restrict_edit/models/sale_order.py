###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_group_readonly = fields.Boolean(
        string='Read Only',
        compute='_compute_is_readonly',
    )

    def _compute_is_readonly(self):
        for order in self:
            order.has_group_readonly = order.user_has_groups(
                'sale_order_group_restrict_edit.group_sale_order_restriction'
            )
