###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    dq_value = fields.Integer(
        string='Data quality',
        compute='_compute_data_quality',
        required=False)

    @api.multi
    def _compute_data_quality(self):
        for template in self:
            value = self.env['data.quality'].compute_rule(template)
            template.dq_value = int(value)
