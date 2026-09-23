###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DocumentExpiry(models.Model):
    _inherit = 'document.expiry'

    ppe_id = fields.Many2one(
        comodel_name='hr.personal.equipment',
        domain='[("employee_id", "=", employee_id)]',
        string='PPE Allocation',
    )

    @api.model
    def _selection_document_type(self):
        value = ('ppe', _('PPE Allocation'))
        result = super()._selection_document_type()
        if value not in result:
            result.append(value)
        return result

    @api.constrains('document_type', 'employee_id', 'ppe_id')
    def _check_ppe_employee(self):
        for document in self.filtered(lambda rec: rec.document_type == 'ppe'):
            if not document.employee_id:
                raise ValidationError(_(
                    'A PPE document requires an employee.'))
            if not document.ppe_id:
                raise ValidationError(_(
                    'A PPE document requires a PPE allocation.'))
            if document.ppe_id.employee_id != document.employee_id:
                raise ValidationError(_(
                    'The PPE allocation must belong to the selected employee.'))
