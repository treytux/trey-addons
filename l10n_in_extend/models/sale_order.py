###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    transport_mode = fields.Char(
        string='Transport Mode',
    )
    vehicle_number = fields.Char(
        string='Vehicle Number',
    )
    supply_date = fields.Char(
        string='Date Supply',
    )
    supply_place = fields.Char(
        string='Place to Supply',
    )

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals.update({
            'transport_mode': self.transport_mode,
            'vehicle_number': self.vehicle_number,
            'supply_date': self.supply_date,
            'supply_place': self.supply_place,
        })
        return vals
