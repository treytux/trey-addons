###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if 'area_id' not in vals:
            res._compute_area_id()
        return res

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if 'area_id' not in vals:
            self._compute_area_id()
        return res

    def _compute_area_id(self):
        for product_tmpl in self.filtered(lambda p: p.is_contract):
            product_tmpl.area_id = (
                product_tmpl.contract_template_id.area_id.id
                if product_tmpl.contract_template_id.area_id else False)

    @api.onchange('contract_template_id')
    def onchange_contract_template_id(self):
        self._compute_area_id()
