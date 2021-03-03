###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class ProductCostCategoryItem(models.Model):
    _name = 'product.cost.category.item'
    _description = 'Product Cost Category Item'

    from_standard_price = fields.Float(
        string='From Cost',
        digits=dp.get_precision('Product Price'),
        required=True,
    )
    to_standard_price = fields.Float(
        string='To Cost',
        digits=dp.get_precision('Product Price'),
        required=True,
    )
    formula = fields.Text(
        string='Formula',
        required=True,
        default='standard_price / '
    )
    category_id = fields.Many2one(
        comodel_name='product.cost.category',
        string='Category',
        required=True,
        ondelete='cascade',
        index=True,
        copy=False
    )
    is_ok = fields.Boolean(
        string='Formula ok',
    )
    sequence = fields.Integer(
        string='Sequence',
    )

    @api.constrains('from_standard_price', 'to_standard_price')
    def check_standard_price_range(self):
        precision = self.env['decimal.precision'].precision_get(
            'Product Price')
        for item in self:
            if float_is_zero(item.from_standard_price, precision) and \
                    float_is_zero(item.to_standard_price, precision):
                raise ValidationError(_(
                    'From Standard Price and To Standard Price is zero'))
            if item.to_standard_price <= item.from_standard_price:
                raise ValidationError(_(
                    'From Standard Price greater To Standard Price'))

    @api.constrains('formula')
    def check_formula(self):
        for item in self:
            try:
                formula = item.formula.replace('standard_price', '50.00')
                float(eval(formula))
                item.is_ok = True
            except ValueError:
                item.is_ok = False
                raise ValidationError(_(
                    'Formula Error: No Return Float Value'))
            except Exception as e:
                item.is_ok = False
                raise ValidationError(_('Formula Error:%s' % e))
