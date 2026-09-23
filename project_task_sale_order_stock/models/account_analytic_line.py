##############################################################################
# For copyright and license notices, see __manifest__.py file in root
# directory
##############################################################################
from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale order line',
        copy=False,
        ondelete='restrict',
    )
