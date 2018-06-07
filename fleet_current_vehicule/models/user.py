# -*- coding: utf-8 -*-
# © 2015 Trey, Kilobytes de Soluciones
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields, exceptions, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    current_vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Current vehicle',
        domain="[('driver_id', '=', partner_id')]")

    @api.multi
    @api.onchange('current_vehicle_id')
    def _onchange_current_vehicle_id(self):
        if self.current_vehicle_id.exists():
            users = self.env['res.users'].search([
                ('current_vehicle_id', '=', self.current_vehicle_id.id)])
            if users.exists():
                raise exceptions.Warning(
                    _('This vehicle is already associated with salesman %s, '
                      'you must choose another.') % users[0].name)
