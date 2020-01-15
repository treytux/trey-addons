###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    unit_id = fields.Many2one(
        comodel_name='product.business.unit',
        string='Business unit',
    )
    area_id = fields.Many2one(
        comodel_name='product.business.area',
        string='Area',
    )

    @api.model
    def create(self, vals):
        unit_obj = self.env['product.business.unit']
        vals.update(unit_obj.force_integrity_unit_and_area(vals))
        return super().create(vals)

    @api.multi
    def write(self, vals):
        unit_obj = self.env['product.business.unit']
        vals.update(unit_obj.force_integrity_unit_and_area(vals, self.area_id))
        return super().write(vals)
