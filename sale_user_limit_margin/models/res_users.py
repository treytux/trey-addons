###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.addons import decimal_precision as dp


class ResUsers(models.Model):
    _inherit = 'res.users'

    sales_margin_limit = fields.Float(
        string='Minimun margin limit per sale order (%)',
        digits=dp.get_precision('Product Price'),
    )
    apply_margin_limit = fields.Boolean(
        sring='Apply margin limit',
    )
