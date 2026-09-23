###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Lot location',
        compute='_compute_location_id',
        store=True,
    )

    @api.depends('lot_id')
    def _compute_location_id(self):
        for asset in self:
            quants = asset.lot_id.quant_ids.filtered(
                lambda q: q.location_id.usage == 'internal'
                and q.quantity == 1)
            if not quants:
                continue
            asset.location_id = quants[0].location_id.id
