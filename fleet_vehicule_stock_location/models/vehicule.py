# -*- coding: utf-8 -*-
# © 2015 Trey, Kilobytes de Soluciones
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, exceptions, _


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    stock_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Stock Location')

    @api.one
    def create_stock_location(self, name, user=None):
        if not user:
            user = self.env.user
        if not user.warehouse_id:
            raise exceptions.Warning(_('Your user has no assigned any '
                                       'warehouse, you must assign one.'))
        return self.env['stock.location'].create({
            'location_id': self.env.user.warehouse_id.lot_stock_id.id,
            'usage': 'internal',
            'name': name})

    @api.model
    def create(self, vals):
        '''Create a location in the stock location of the user warehouse.'''
        if 'stock_location_id' not in vals:
            loc_id = self.create_stock_location(vals['license_plate'])
            vals['stock_location_id'] = loc_id.id
        return super(FleetVehicle, self).create(vals)
