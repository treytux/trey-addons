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
        res = super().product_id_change()
        if not self.product_id:
            self.supplierinfo_id = False
            return
        self.supplierinfo_id = (
            self.product_id.seller_ids and self.product_id.seller_ids[0].id
            or None)
        self.vendor_id = (
            self.product_id.seller_ids
            and self.product_id.seller_ids[0].partner_id.id or None)
        return res

    @api.onchange('supplierinfo_id')
    def _onchange_supplierinfo_id(self):
        self.vendor_id = self._get_vendor_from_supplierinfo(
            self.supplierinfo_id)

    @api.model
    def _get_vendor_from_supplierinfo(self, supplierinfo):
        if not supplierinfo:
            return False
        if isinstance(supplierinfo, models.BaseModel):
            return supplierinfo.partner_id.id
        return self.env['product.supplierinfo'].browse(
            supplierinfo).partner_id.id

    @api.model
    def _prepare_supplierinfo_vendor_vals(self, vals):
        if 'supplierinfo_id' not in vals:
            return vals
        vals['vendor_id'] = self._get_vendor_from_supplierinfo(
            vals.get('supplierinfo_id'))
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [
            self._prepare_supplierinfo_vendor_vals(dict(vals))
            for vals in vals_list
        ]
        return super().create(vals_list)

    def write(self, vals):
        vals = self._prepare_supplierinfo_vendor_vals(dict(vals))
        return super().write(vals)

    @api.constrains('supplierinfo_id')
    def _check_supplierinfo(self):
        for line in self:
            if not line.supplierinfo_id:
                continue
            if line.supplierinfo_id.product_id == line.product_id:
                continue
            template = line.product_id.product_tmpl_id
            if line.supplierinfo_id.product_tmpl_id == template:
                continue
            raise exceptions.ValidationError(_(
                'Supplier info must be for the same product that the line'))

    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id)
        if self.supplierinfo_id:
            values['supplierinfo_id'] = self.supplierinfo_id
        return values
