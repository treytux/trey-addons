###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    signing_identifier = fields.Char(
        string='Signing identifier',
    )

    @api.constrains('signing_identifier')
    def _check_signing_identifier_duplicated(self):
        for record in self:
            if record.signing_identifier is False:
                continue
            employees = self.env['hr.employee'].search([
                ('signing_identifier', '=', record.signing_identifier),
            ])
            if len(employees) > 1:
                raise exceptions.ValidationError(
                    _('The identifier for signing %s already exists') % (
                        record.signing_identifier))
