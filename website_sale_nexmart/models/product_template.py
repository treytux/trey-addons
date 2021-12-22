###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    show_nexmart_data = fields.Boolean(
        string='Show Nexmart data',
    )
