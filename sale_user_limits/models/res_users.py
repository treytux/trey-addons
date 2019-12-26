###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.addons import decimal_precision as dp


class ResUsers(models.Model):
    _inherit = 'res.users'

    sales_amount_limit = fields.Float(
        string='Max amount without taxes free operation',
        digits=dp.get_precision('Product Price'),
    )
    sales_discount_limit = fields.Float(
        string='Max discount per sale order line (%)',
        digits=dp.get_precision('Product Price'),
    )
