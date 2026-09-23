###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    maintenance_product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Maintenance product template',
        help='''Product that will be added as an order line to all sales
        orders that are created.\nThe price of said line is calculated by
        adding the percentages of the unit prices of the products that affect
        maintenance (those with the "Not increase check maintenance price?"
        disabled on the line) as follows:\n
        \t- If it is greater than the minimum price established in the
        maintenance product ("Sales price" field), the calculated price is
        assigned.
        \t- If it is less than the minimum price established in the
        maintenance product ("Sales price" field), the unit price configured
        in the maintenance product is assigned.''',
    )
