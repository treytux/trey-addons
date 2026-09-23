###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################

from odoo import _, fields, models


class DocumentExpiry(models.Model):
    _inherit = 'document.expiry'

    ppe_id = fields.Many2one(
        comodel_name='hr.employee.ppe',
        domain='[("employee_id", "=", employee_id)]',
    )

    def _selection_document_type(self):
        value = ('ppe', _('PPE Allocation'))
        result = super()._selection_document_type()
        if self.env.context.get('default_owner_type', False) == 'employee' \
                and value not in result:
            result.append(value)
        return result
