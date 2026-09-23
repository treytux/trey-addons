###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.exceptions import UserError


class StockDistribution(models.TransientModel):
    _inherit = 'stock.distribution'

    def get_stock_picking_line_data(
            self, line, new_picking, location_id, sale_line):
        data = super().get_stock_picking_line_data(
            line, new_picking, location_id, sale_line)
        if (
                line.delivery_carrier_id and line.delivery_carrier_id
                != new_picking.carrier_id
        ):
            new_picking.carrier_id = line.delivery_carrier_id.id
        return data

    def check_delivery_carrier(self):
        distribution = {}
        for line in self.confirm_line_ids:
            key = line.location_id.id
            distribution.setdefault(key, []).append(line)
        for _location_id, lines in distribution.items():
            delivery_carrier_ids = set(
                line.delivery_carrier_id for line in lines)
            if len(delivery_carrier_ids) > 1:
                raise UserError(
                    'You cannot distribute products with different delivery '
                    'carriers in the same location. Please select a single '
                    'delivery carrier for each location.')

    def action_confirm_distribution(self):
        self.check_delivery_carrier()
        res = super().action_confirm_distribution()
        return res


class StockDistributionConfirmLine(models.TransientModel):
    _inherit = 'stock.distribution.confirm.line'

    delivery_carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Delivery carrier',
    )
