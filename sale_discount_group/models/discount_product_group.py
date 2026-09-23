###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class DiscountProductGroup(models.Model):
    _name = 'discount.product.group'
    _description = 'Discount product group'

    name = fields.Char(
        string='Group',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company.id,
    )
    product_ids = fields.Many2many(
        comodel_name='product.template',
        compute='_compute_product_ids',
        inverse='_inverse_product_ids',
        string='Products',
    )

    @api.depends('company_id')
    def _compute_product_ids(self):
        template_model = self.env['product.template'].with_context(
            active_test=False)
        for group in self:
            group.product_ids = template_model.search([
                ('dto_group_id', '=', group.id),
            ])

    def _inverse_product_ids(self):
        template_model = self.env['product.template'].with_context(
            active_test=False)
        for group in self:
            current_products = template_model.search([
                ('dto_group_id', '=', group.id),
            ])
            removed_products = current_products - group.product_ids
            added_products = group.product_ids - current_products
            if removed_products:
                removed_products.write({'dto_group_id': False})
            if added_products:
                added_products.write({'dto_group_id': group.id})
