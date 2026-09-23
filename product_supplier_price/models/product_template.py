###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    supplier_cost = fields.Float(
        string='Supplier cost',
        compute='_compute_supplier_cost',
        store=False,
    )

    @api.depends('product_variant_ids', 'product_variant_ids.supplier_cost')
    def _compute_supplier_cost(self):
        for template in self:
            if len(template.product_variant_ids) > 1:
                template.supplier_cost = 0
                continue
            template.supplier_cost = template.product_variant_ids.supplier_cost
