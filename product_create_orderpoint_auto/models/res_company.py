###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    warehouse_auto_orderpoint_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        relation='company2warehouse_rel',
        column1='company_id',
        column2='warehouse_id',
        required=True,
        help='Warehouses for which a reordering rule will be created '
             'automatically when a product is created.',
    )
