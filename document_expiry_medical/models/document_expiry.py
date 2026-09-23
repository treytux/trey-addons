###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################

from odoo import _, fields, models


class DocumentExpiry(models.Model):
    _inherit = 'document.expiry'

    examination_id = fields.Many2one(
        comodel_name='hr.employee.medical.examination',
        domain='[("employee_id", "=", employee_id)]',
        string='Medical Examination',
    )

    def _selection_document_type(self):
        value = ('medical', _('Medical Examination'))
        result = super()._selection_document_type()
        if self.env.context.get('default_owner_type', False) == 'employee' \
                and value not in result:
            result.append(value)
        return result
