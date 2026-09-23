###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class DocumentExpiry(models.Model):
    _inherit = 'document.expiry'

    examination_id = fields.Many2one(
        comodel_name='hr.employee.medical.examination',
        domain='[("employee_id", "=", employee_id)]',
        string='Medical Examination',
    )

    @api.model
    def _selection_document_type(self):
        value = ('medical', _('Medical Examination'))
        result = super()._selection_document_type()
        if (self.env.context.get('default_owner_type') == 'employee'
                and value not in result):
            result.append(value)
        return result

    @api.model_create_multi
    def create(self, vals_list):
        if any(
                vals.get('owner_type') == 'employee'
                or vals.get('employee_id')
                for vals in vals_list
        ):
            self = self.with_context(default_owner_type='employee')
        return super().create(vals_list)
