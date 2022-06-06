###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    supplierinfo_id = fields.Many2one(
        comodel_name='product.supplierinfo',
        string='Vendor',
        domain='["|",'
               '("product_id", "=", product_id),'
               '("product_tmpl_id.product_variant_ids", "in", [product_id])]',
    )

    @api.onchange('product_id')
    def product_id_change(self):
        super().product_id_change()
        if not self.product_id:
            self.supplierinfo_id = False
            return
        self.supplierinfo_id = (
            self.product_id.seller_ids and self.product_id.seller_ids[0].id
            or None)
        self.vendor_id = (
            self.product_id.seller_ids
            and self.product_id.seller_ids[0].name.id or None)

    @api.constrains('supplierinfo_id')
    def _check_supplierinfo(self):
        for line in self:
            if not self.supplierinfo_id:
                continue
            if self.supplierinfo_id.product_id == line.product_id:
                continue
            template = line.product_id.product_tmpl_id
            if self.supplierinfo_id.product_tmpl_id == template:
                continue
            raise exceptions.ValidationError(_(
                'Supplier info must be for the same product that the line'))
