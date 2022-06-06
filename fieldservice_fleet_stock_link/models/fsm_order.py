###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FSMOrder(models.Model):
    _inherit = 'fsm.order'

    assigned_partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='person_id.partner_id',
    )
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        domain='[("driver_id", "=", assigned_partner_id)]',
    )
    warehouse_id = fields.Many2one(
        domain='[("vehicle_id", "=", vehicle_id),("vehicle_id", "!=", False)]',
    )

    @api.constrains('warehouse_id', 'person_id', 'vehicle_id')
    def _check_warehouse_person(self):
        for order in self:
            if not order.person_id and not order.vehicle_id:
                continue
            if order.vehicle_id.driver_id != order.assigned_partner_id:
                raise ValidationError(
                    _('Vehicle %s is not assigned to driver %s')
                    % (order.vehicle_id.name, order.assigned_partner_id.name))
            if order.warehouse_id.vehicle_id != order.vehicle_id:
                raise ValidationError(
                    _('Warehouse %s is not assigned to one of worker vehicles')
                    % order.warehouse_id.name)

    @api.onchange('person_id', 'vehicle_id')
    def _onchange_warehouse_relations(self):
        if not self.person_id:
            self.vehicle_id = False
            self.warehouse_id = self.env.ref('stock.warehouse0').id
        else:
            vehicles = self.env['fleet.vehicle'].search([
                ('driver_id', '=', self.person_id.partner_id.id)
            ])
            if not vehicles:
                self.vehicle_id = self.warehouse_id = False
            else:
                if (not self.vehicle_id
                        or self.person_id.partner_id
                        not in self.vehicle_id.driver_id):
                    self.vehicle_id = vehicles[0].id
                self.warehouse_id = (
                    self.vehicle_id.warehouse_ids
                    and self.vehicle_id.warehouse_ids[0].id
                    or None)
