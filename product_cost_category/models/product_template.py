###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare, float_is_zero


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cost_category_price = fields.Float(
        string='Cost Category Price',
        digits=dp.get_precision('Product Price'),
        compute='compute_template_cost_category_price',
        store=True,
    )

    @api.multi
    @api.depends('product_variant_ids', 'product_variant_ids.standard_price')
    def compute_template_cost_category_price(self):
        for template in self:
            update_type = self.env['ir.config_parameter'].sudo().get_param(
                key='product_cost_category.cost_category_price_setting',
                default='manual')
            if update_type == 'manual':
                return
            category_id = self.env['product.cost.category'].search([
                ('date_start', '<=', fields.Date.today()),
                ('date_end', '>=', fields.Date.today())], limit=1)
            if not category_id:
                return
            price = self.calculate_category_price(category_id=category_id)
            if price:
                template.calculate_category_price = price

    def calculate_category_price(self, category_id=None):
        rounding = self.env.user.company_id.currency_id.rounding
        if len(self.product_variant_ids) <= 1:
            if float_is_zero(
                    self.standard_price, precision_rounding=rounding):
                return False
        category_item = category_id.mapped('item_ids').filtered(
            lambda i:
                i.from_standard_price
                <= self.standard_price
                <= i.to_standard_price
        )
        if not category_item:
            return False
        if self.product_variant_ids == 1:
            return eval(category_item.formula.replace(
                'standard_price', str(self.standard_price)))
        for variant in self.product_variant_ids:
            if float_is_zero(
                    variant.standard_price, precision_rounding=rounding):
                continue
            if float_compare(variant.standard_price, self.standard_price,
                             precision_rounding=rounding) == 0:
                variant.cost_category_price = self.cost_category_price
                continue
            variant_category_item = category_id.mapped(
                'item_ids').filtered(
                lambda i:
                    i.from_standard_price
                    <= variant.standard_price
                    <= i.to_standard_price
            )
            variant.cost_category_price = eval(
                variant_category_item.formula.replace(
                    'standard_price', str(variant.standard_price)))
            return False
