###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        if not vals.get('contract_template_id'):
            return super().create(vals)
        template = self.env['contract.template'].browse(
            vals['contract_template_id'])
        if template.unit_id:
            vals['unit_id'] = template.unit_id.id
        if template.area_id:
            vals['area_id'] = template.area_id.id
        return super().create(vals)

    @api.multi
    def write(self, vals):
        if not vals.get('contract_template_id'):
            return super().write(vals)
        template = self.env['contract.template'].browse(
            vals['contract_template_id'])
        if template.unit_id:
            vals['unit_id'] = template.unit_id.id
        if template.area_id:
            vals['area_id'] = template.area_id.id
        return super().write(vals)

    @api.onchange('contract_template_id')
    def onchange_contract_template_id(self):
        if not self.contract_template_id:
            return
        template = self.contract_template_id
        if template.unit_id:
            self.unit_id = template.unit_id.id
        if template.area_id:
            self.area_id = template.area_id.id
