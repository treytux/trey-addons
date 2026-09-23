###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_account_sales_refund_id = fields.Many2one(
        comodel_name='account.account',
        string='Sales return account',
    )
    property_account_purchase_refund_id = fields.Many2one(
        comodel_name='account.account',
        string='Purchase return account',
    )
