###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.addons import decimal_precision as dp


class ProductStandardPriceHistory(models.Model):
    _name = 'product.standard_price.history'
    _description = 'Product standard price history'

    def _get_default_company_id(self):
        return self._context.get('force_company', self.env.user.company_id.id)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=_get_default_company_id,
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        ondelete='cascade',
        required=True,
    )
    datetime = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
    )
    standard_price = fields.Float(
        string='Product cost',
        group_operator='avg',
        digits=dp.get_precision('Product Price'),
    )
