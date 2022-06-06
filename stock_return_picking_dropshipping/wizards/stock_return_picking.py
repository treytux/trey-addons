###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.model
    def _get_domain_location_id(self):
        picking = self.env['stock.picking'].browse(
            self.env.context.get('active_id', None))
        dropship_picking_type = self.env.ref(
            'stock_dropshipping.picking_type_dropship')
        original_location_id = picking.location_id.id
        default_domain = [
            '|',
            ('id', '=', original_location_id),
            ('return_location', '=', True)]
        if picking.picking_type_id != dropship_picking_type:
            return default_domain
        internal_locations = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
        ])
        domain = default_domain + [('id', 'in', internal_locations.ids)]
        domain.insert(0, '|')
        return domain

    location_id = fields.Many2one(
        domain=_get_domain_location_id,
    )
