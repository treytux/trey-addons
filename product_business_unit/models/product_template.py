###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    unit_id = fields.Many2one(
        comodel_name='product.business.unit',
        string='Business unit',
    )
    area_id = fields.Many2one(
        comodel_name='product.business.area',
        string='Area',
    )
    business_display_name = fields.Char(
        string='Business Display Name',
        compute='_compute_business_display_name',
    )

    @api.multi
    @api.depends('unit_id', 'area_id')
    def _compute_business_display_name(self):
        for product in self:
            product.business_display_name = '/'.join(
                [s for s in [product.unit_id.name, product.area_id.name] if s])

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
