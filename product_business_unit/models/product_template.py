###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    unit_id = fields.Many2one(
        comodel_name='product.business.unit',
        compute='_compute_unit_id',
        readonly=True,
        store=True,
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

    @api.model
    def business_display_name_get(self, record):
        unit = getattr(record, 'unit_id')
        area = getattr(record, 'area_id')
        return ' / '.join([s.name for s in [unit, area] if s])

    @api.multi
    @api.depends('area_id')
    def _compute_unit_id(self):
        for product in self:
            product.unit_id = (
                product.area_id.unit_id.id if product.area_id else False)

    @api.multi
    @api.depends('unit_id', 'area_id')
    def _compute_business_display_name(self):
        for product in self:
            product.business_display_name = self.business_display_name_get(
                product)

    @api.model
    def check_area_id(self, records):
        errors = records.filtered(
            lambda r: r.area_id and r.unit_id and
            r.area_id.unit_id != r.unit_id)
        if not errors:
            return
        names = '\n'.join(errors.mapped('name'))
        raise ValidationError(_(
            'The Business defined must be equal to Area Business for next '
            '%s:\n%') % (records[0]._description, names))

    @api.multi
    @api.constrains('unit_id', 'area_id')
    def _check_area_id(self):
        self.check_area_id(self)
