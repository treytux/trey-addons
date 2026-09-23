###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
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

    @api.depends('standard_price')
    def _compute_template_cost_category_price(self):
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
        for template in self:
            if len(template.product_variant_ids) != 1:
                return False
            if float_is_zero(
                    template.standard_price, precision_rounding=rounding):
                return False
            category_item = category_id.mapped('item_ids').filtered(
                lambda i:
                    i.from_standard_price
                    <= template.standard_price
                    <= i.to_standard_price
            )
            if not category_item:
                return False
            template.cost_category_price = eval(category_item.formula.replace(
                'standard_price', str(self.standard_price)))
