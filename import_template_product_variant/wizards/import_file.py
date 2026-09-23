###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ImportFile(models.TransientModel):
    _inherit = 'import.file'

    def get_data_row(self, wizard_tmpl_model, model, df, row):
        data, all_errors = super().get_data_row(
            wizard_tmpl_model, model, df, row)
        wizard_model = self.template_id.model_id.model
        if wizard_model == 'import.template.product.variant':
            new_errors = []
            for _count, error in enumerate(all_errors):
                if '*TMPL*' not in error:
                    new_errors.append(error)
            return data, new_errors
        return data, all_errors
