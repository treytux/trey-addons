###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    non_preferred_supplier = fields.Boolean(
        string='Non-preferred supplier',
    )

    @api.onchange('non_preferred_supplier')
    def onchange_non_preferred_supplier(self):
        if isinstance(self.id, models.NewId):
            partner_id = self._origin.id
        elif isinstance(self.id, int):
            partner_id = self.id
        if self.non_preferred_supplier:
            supplierinfos = self.env['product.supplierinfo'].search([
                ('name', '=', partner_id),
            ])
            for info in supplierinfos:
                infos = self.env['product.supplierinfo'].search([
                    ('product_tmpl_id', '=', info.product_tmpl_id.id),
                ])
                infos_prefer = infos.filtered(
                    lambda s: not s.name.non_preferred_supplier) - info
                if infos_prefer:
                    info.write({
                        'sequence': max(infos_prefer.mapped('sequence')) + 1
                    })
