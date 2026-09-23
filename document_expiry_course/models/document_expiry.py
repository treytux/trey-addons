###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class DocumentExpiry(models.Model):
    _inherit = 'document.expiry'

    course_id = fields.Many2one(
        comodel_name='hr.course',
    )

    @api.model
    def _selection_document_type(self):
        value = ('course', _('Course'))
        result = super()._selection_document_type()
        if value not in result:
            result.append(value)
        return result
