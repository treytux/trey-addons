# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import _, api, models


class ImportFile(models.TransientModel):
    _inherit = 'import.file'

    @api.multi
    def get_data_row(self, wizard_tmpl_model, model, df, row):
        data, all_errors = super(ImportFile, self).get_data_row(
            wizard_tmpl_model, model, df, row)
        if wizard_tmpl_model._model._name != 'import.template.sale_beezup':
            return data, all_errors
        clean_errors = all_errors[:]
        for error in all_errors:
            if _('is not a field for model') in error:
                clean_errors.remove(error)
        return data, clean_errors
