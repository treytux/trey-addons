###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class QcUseDate(models.Model):
    _name = 'qc.use.date'
    _description = 'Quality control use date'

    date = fields.Date(
        string='Use date',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot',
    )
