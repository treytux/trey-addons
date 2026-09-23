###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class DeliveryCarrierManifest(models.Model):
    _name = 'delivery.carrier.manifest'
    _description = 'Delivery Carrier Manifest'

    name = fields.Char(
        string='Name',
        required=True,
        copy=False,
    )
    carrier_id = fields.Many2one(
        string='Carrier',
        comodel_name='delivery.carrier',
        required=True,
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.user.company_id.id,
    )
    picking_ids = fields.One2many(
        string='Pickings',
        comodel_name='stock.picking',
        inverse_name='manifest_id',
    )

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'delivery.carrier.manifest')
        res = super().create(vals)
        carrier_code = res.carrier_id.product_id.default_code or ''
        if carrier_code:
            res.name = res.name.replace('MANIF', carrier_code)
        return res
