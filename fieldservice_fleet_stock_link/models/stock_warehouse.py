###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Vehicle',
    )

    @api.constrains('vehicle_id')
    def _check_vehicle_id(self):
        for warehouse in self:
            if not warehouse.vehicle_id:
                continue
            warehouses = self.search([
                ('vehicle_id', '=', warehouse.vehicle_id.id),
            ])
            if len(warehouses) > 1:
                raise ValidationError(
                    _('Vehicle assigned in multiple warehouses: %s')
                    % ", ".join(warehouses.mapped('name')))
