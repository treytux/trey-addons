###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    route_select = fields.Selection(
        selection=[
            ('product', 'Use product route'),
            ('customize', 'Customize route'),
        ],
        string='Route',
        default='product',
        required=True,
    )
    route_ids = fields.Many2many(
        comodel_name='stock.location.route',
        relation='product_supplierinfo2stock_location_route_rel',
        column1='supplierinfo_id',
        column2='route_id',
        string='Customize Route',
        domain='[("product_selectable", "=", True)]',
        help='Apply specific route(s) for the replenishment instead of '
             'product\'s default routes.',
    )
