###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cost_category_price = fields.Float(
        string='Cost Category Price',
        digits=dp.get_precision('Product Price'),
        compute='_compute_template_cost_category_price',
        store=True,
    )

    @api.one
    @api.depends('product_variant_ids.standard_price', 'standard_price')
    def _compute_template_cost_category_price(self):
        price = self.calculate_cost_category_price(template=self)
        if price:
            self.cost_category_price = price

    def calculate_cost_category_price(self, template=None, product=None):
        update_type = self.env['ir.config_parameter'].sudo().get_param(
            key='product_cost_category.sale_price_update_setting',
            default='manual')
        active_model = self.env.context.get('active_model', False)
        if update_type == 'manual' and active_model == 'product.template' \
                and not self.env.context.get('update_from_wizard'):
            return False
        if update_type == 'manual' and active_model == 'product.product' and\
                not self.env.context.get('update_from_wizard'):
            return False
        if update_type == 'manual' and active_model:
            return False
        if self.env.context.get('selection_category'):
            cost_category = self.env.context.get('selection_category')
        else:
            cost_category = self.env['product.cost.category'].search([
                ('date_start', '<=', fields.Date.today()),
                ('date_end', '>=', fields.Date.today())], limit=1)
        if not cost_category:
            return False
        rounding = self.env.user.company_id.currency_id.rounding
        if template:
            cost_category_item = cost_category.mapped('item_ids').filtered(
                lambda i:
                i.from_standard_price <= template.standard_price <=
                i.to_standard_price)
            if not cost_category_item:
                return False
            for product in self.product_variant_ids:
                if not float_is_zero(
                        product.standard_price, precision_rounding=rounding)\
                        and product.cost_category_price == \
                        self.cost_category_price:
                    product.cost_category_price = template.cost_category_price
                else:
                    product.cost_category_price = eval(
                        cost_category_item.formula.replace(
                            'standard_price', str(product.standard_price)))
            return eval(cost_category_item.formula.replace(
                'standard_price', str(self.standard_price)))
        if product:
            if float_is_zero(
                    product.standard_price, precision_rounding=rounding) and\
                    product.cost_category_price == \
                    product.product_tmpl_id.cost_category_price:
                return product.product_tmpl_id.cost_category_price
            else:
                cost_category_item = cost_category.mapped('item_ids').filtered(
                    lambda i:
                    i.from_standard_price <= product.standard_price <=
                    i.to_standard_price)
                if not cost_category_item:
                    return False
                return eval(cost_category_item.formula.replace(
                    'standard_price', str(product.standard_price)))
        return False
