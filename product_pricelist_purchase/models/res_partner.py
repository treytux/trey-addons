###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    supplier_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist.purchase',
        string='Supplier pricelist',
    )
