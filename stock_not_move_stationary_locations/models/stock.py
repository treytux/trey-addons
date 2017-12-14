# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, exceptions, _


class StockLocation(models.Model):
    _inherit = 'stock.location'

    @api.one
    def write(self, vals):
        if 'location_id' in vals:
            vehicles = self.env['fleet.vehicle'].search(
                [('stock_location_id', '=', self.id)])
            if not vehicles.exists():
                raise exceptions.Warning(_(
                    'It is not allowed to move a location that is not '
                    'associated with a vehicle.'))
        return super(StockLocation, self).write(vals)
