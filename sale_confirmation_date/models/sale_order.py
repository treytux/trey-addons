###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    confirmation_date = fields.Datetime(
        string='Confirmation Date',
        readonly=True,
        copy=False,
        help='Confirmation date of confirmed orders.',
    )

    def _prepare_confirmation_values(self):
        res = super()._prepare_confirmation_values()
        res.update({
            'confirmation_date': res.pop('date_order'),
        })
        return res
