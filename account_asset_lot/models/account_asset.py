###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Lot location',
        compute='_compute_location_id',
        store=True,
    )

    @api.depends('lot_id')
    def _compute_location_id(self):
        for asset in self.filtered('lot_id'):
            quants = self.env['stock.quant'].search([
                ('lot_id', '=', asset.lot_id.id),
                ('location_id.usage', '=', 'internal'),
                ('quantity', '=', 1)
            ])
            asset.location_id = quants[:1].location_id
