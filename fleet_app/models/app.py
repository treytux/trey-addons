# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
import logging
_log = logging.getLogger(__name__)


class App(models.AbstractModel):
    _inherit = 'app'

    @api.model
    def get_stock_location(self):
        loc_id = (self.env.user.current_vehicle_id and
                  self.env.user.current_vehicle_id.stock_location_id or
                  None)
        if not loc_id:
            _log.warning('get_stock_location: No location for %s' % (
                self.env.user.name))
            return super(App, self).get_stock_location()
        _log.info('get_stock_location: Location "%s" %s' % (
            loc_id.name, loc_id.id))
        products = self.env['product.product'].with_context({
            'location': loc_id.id}).sudo().search(
                [('location_id', '=', loc_id.id)],
                order='name asc')
        return {
            'id': loc_id.id,
            'code': loc_id.name,
            'products': [{
                'id': p.id,
                'name': ' '.join(
                    [p.name] + [a.name
                                for a in p.attribute_value_ids]),
                'qty_available': p.qty_available,
                'uom_name': p.uom_id.name,
                'image': p.image_small
            } for p in products] if products else []}
