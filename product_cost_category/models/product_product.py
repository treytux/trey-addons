###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero


class ProductProduct(models.Model):
    _inherit = 'product.product'

    cost_category_price = fields.Float(
        string='Cost Category Price',
        digits=dp.get_precision('Product Price'),
        compute='_compute_product_cost_category_price',
        store=True,
    )

    @api.depends('standard_price')
    def _compute_product_cost_category_price(self):
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
        rounding = self.env.user.company_id.currency_id.rounding
        for product in self:
            product_category_item = category_id.mapped('item_ids').filtered(
                lambda i:
                    i.from_standard_price
                    <= product.standard_price
                    <= i.to_standard_price
            )
            if not product_category_item:
                continue
            if float_is_zero(
                    product.standard_price, precision_rounding=rounding):
                continue
            product.cost_category_price = eval(
                product_category_item.formula.replace(
                    'standard_price', str(product.standard_price)))

    @api.multi
    def price_compute(
            self, price_type, uom=False, currency=False, company=False):
        res = super().price_compute(price_type, uom, currency, company)
        rounding = self.env.user.company_id.currency_id.rounding
        if price_type != 'cost_category_price':
            return res
        if not uom and self._context.get('uom'):
            uom = self.env['uom.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(
                self._context['currency'])
        prices = dict.fromkeys(self.ids, 0.0)
        for product in self:
            prices[product.id] = product.cost_category_price or 0.00
            if float_is_zero(
                    prices[product.id], precision_rounding=rounding):
                product.cost_category_price = (
                    product.product_tmpl_id.cost_category_price)
                prices[product.id] = product.cost_category_price or 0.00
            prices[product.id] += product.price_extra
            if self._context.get('no_variant_attributes_price_extra'):
                prices[product.id] += sum(
                    self._context.get('no_variant_attributes_price_extra'))
            if uom:
                prices[product.id] = product.uom_id._compute_price(
                    prices[product.id], uom)
            if currency:
                prices[product.id] = product.currency_id._convert(
                    prices[product.id], currency, product.company_id,
                    fields.Date.today())
        return prices
