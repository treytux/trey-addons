###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.model
    def create(self, vals):
        partner = self.env['res.partner'].browse(vals['name'])
        infos = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', vals['product_tmpl_id']),
        ])
        no_prefer = infos.filtered(
            lambda s: s.name.non_preferred_supplier)
        if no_prefer and not partner.non_preferred_supplier:
            vals['sequence'] = min(no_prefer.mapped('sequence')) - 1
        elif infos and partner.non_preferred_supplier:
            vals['sequence'] = max(infos.mapped('sequence')) + 1
        res = super().create(vals)
        return res

    @api.multi
    def write(self, vals):
        for info in self:
            infos = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', info.product_tmpl_id.id),
            ])
            no_prefer = infos.filtered(
                lambda s: s.name.non_preferred_supplier)
            if any([f in vals for f in ['sequence', 'price', 'min_qty']]):
                if (no_prefer and (vals.get('sequence')
                    and vals['sequence'] >= min(no_prefer.mapped('sequence')))
                        and not info.name.non_preferred_supplier):
                    vals['sequence'] = min(no_prefer.mapped('sequence')) - 1
                elif infos and info.name.non_preferred_supplier:
                    vals['sequence'] = max(infos.mapped('sequence')) + 1
        res = super().write(vals)
        return res
