###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    margin = fields.Float(
        string='Margin (%)',
        digits=dp.get_precision('Discount'),
        compute='_compute_margin',
        inverse='_inverse_margin',
        search='_search_margin',
    )
    list_price = fields.Float(
        compute='_compute_list_price',
        store=True,
        readonly=False,
    )

    @api.model
    def create(self, vals):
        if self._context.get('create_from_tmpl'):
            return super().create(vals)
        if 'margin' not in vals:
            return super().create(vals)
        self = self.with_context(force_margin=vals['margin'])
        return super(ProductTemplate, self).create(vals)

    @api.depends('product_variant_ids', 'product_variant_ids.margin')
    def _compute_margin(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.margin = template.product_variant_ids.margin

    def _search_margin(self, operator, value):
        products = self.env['product.product'].search(
            [('margin', operator, value)], limit=None)
        return [('id', 'in', products.mapped('product_tmpl_id').ids)]

    @api.multi
    def _inverse_margin(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.margin = template.margin

    @api.onchange('standard_price', 'margin')
    def _compute_list_price(self):
        for template in self:
            if len(template.product_variant_ids) > 1:
                template.list_price = max(
                    template.product_variant_ids.mapped('lst_price'))
                continue
            if not template.standard_price:
                continue
            if template.margin >= 100:
                template.margin = 99.99
            margin = template.margin and (template.margin / 100) or 0
            template.list_price = template.standard_price / (1 - margin)

    @api.onchange('list_price')
    def onchange_list_price(self):
        if not self.standard_price or not self.list_price:
            self.margin = 0
            return
        margin = self.standard_price / self.list_price
        margin = (margin - 1) * -100
        self.margin = margin >= 100 and 99.99 or margin

    def price_compute(self, price_type, uom=False, currency=False,
                      company=False):
        if price_type == 'variant_lst_price':
            return {
                t.id: max(t.product_variant_ids.mapped('lst_price'))
                for t in self
            }
        return super().price_compute(
            price_type, uom=uom, currency=currency, company=company)
