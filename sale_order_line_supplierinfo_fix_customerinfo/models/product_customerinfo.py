###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductCustomerInfo(models.Model):
    _inherit = 'product.customerinfo'

    route_ids = fields.Many2many(
        comodel_name='stock.route',
        relation='product_customerinfo2stock_location_route_rel',
        column1='customerinfo_id',
        column2='route_id',
        string='Customize Route',
        domain='[("product_selectable", "=", True)]',
    )
