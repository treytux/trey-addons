###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ContractLine(models.Model):
    _inherit = 'contract.line'

    contract_generation_type = fields.Selection(
        related='contract_id.generation_type',
        string='Contract Generation Type',
        readonly=True,
    )
    route_id = fields.Many2one(
        comodel_name='stock.route',
        string='Route',
        domain=[
            ('sale_selectable', '=', True),
        ],
        ondelete='restrict',
        check_company=True,
        help='Route to be used in the sale order line generated from this '
        'contract line.',
    )

    def _prepare_sale_line_vals(self, dates, order_id=False):
        vals = super()._prepare_sale_line_vals(dates, order_id=order_id)
        if self.route_id:
            vals['route_id'] = self.route_id.id
        return vals
