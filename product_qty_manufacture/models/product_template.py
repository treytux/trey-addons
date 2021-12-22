###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


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
        digits=dp.get_precision('Product Unit of Measure'),
        help='Quantity of stock compute from BoM.',
    )

    def action_report_mrp_bom(self):
        return self.product_variant_id.action_report_mrp_bom()

    @api.one
    def _set_stock_bom_id(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.stock_bom_id = self.stock_bom_id
