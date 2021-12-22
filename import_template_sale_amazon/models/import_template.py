###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ImportTemplate(models.Model):
    _inherit = 'import.template'

    @api.multi
    @api.depends('model_id')
    def _compute_template_file_name(self):
        super()._compute_template_file_name()
        for template in self:
            if template.model_id.model == 'import.template.sale_amazon':
                template.template_file_name = 'template_sale_amazon.txt'
