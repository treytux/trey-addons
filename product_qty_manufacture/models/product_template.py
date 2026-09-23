from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        related='product_variant_id.stock_bom_id',
        inverse='_set_stock_bom_id',
        readonly=False,
        domain='[("product_tmpl_id", "=", id)]',
        string='BoM for compute manufacture stock',
    )
    qty_manufacture = fields.Float(
        string='Manufacture',
        related='product_variant_id.qty_manufacture',
        help='Quantity of stock compute from BoM.',
    )

    def action_report_mrp_bom(self):
        return self.product_variant_id.action_report_mrp_bom()

    def _set_stock_bom_id(self):
        for product_tmpl in self:
            if len(product_tmpl.product_variant_ids) == 1:
                product_tmpl.product_variant_ids.stock_bom_id = (
                    product_tmpl.stock_bom_id
                )
