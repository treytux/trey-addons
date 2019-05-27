###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    website_pricelist_ids = fields.Many2many(
        comodel_name='product.pricelist')
