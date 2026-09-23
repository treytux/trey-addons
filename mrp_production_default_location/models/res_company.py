###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    mrp_location_src_id = fields.Many2one(
        comodel_name='stock.location',
        string='Mrp raw materials location',
        help='Raw material location to assign in manufacturing orders. If it '
        'is empty, will use default stock location.',
    )
    mrp_location_dst_id = fields.Many2one(
        comodel_name='stock.location',
        string='Mrp finished Products Location',
        help='Finished products location to assign in manufacturing orders. '
        'If it is empty, will use default stock location.',
    )
