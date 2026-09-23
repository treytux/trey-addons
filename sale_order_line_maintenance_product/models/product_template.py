###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    maintenance_percentage = fields.Float(
        string='Maintenance percentage',
        help='Indicates the percentage that will increase the maintenance '
             'product template.',
    )
