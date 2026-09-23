###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    barcode_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Barcode sequence',
    )
