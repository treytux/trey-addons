###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class DocumentExpiry(models.Model):
    _inherit = 'document.expiry'

    owner_type = fields.Selection(
        selection_add=[
            ('employee', 'Employee')
        ],
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        ondelete='restrict',
    )
    warn_employee = fields.Boolean()

    @api.model
    def _get_expired_group(self):
        self.ensure_one()
        if self.owner_type == 'employee':
            return self.env.ref(
                'document_expiry_employee.document_employee_expiry_warn')
        return super()._get_expired_group()

    @api.model
    def _get_summary(self, state, owner_type):
        result = super()._get_summary(state, owner_type)
        if owner_type == 'employee':
            return _(
                'Employee\'s documentation in state {}'.format(state.name))
        return result

    @api.model
    def document_expiry_warn_employee(self):
        Status = self.env['document.expiry.status']
        self._update_document_expiry_status()
        xml_id = 'document_expiry_employee.' \
                 'activity_document_expired_warn_employee'
        for state in Status.search([('warn', '=', True)]):
            domain = [
                ('status_id', '=', state.id),
                ('owner_type', '=', 'employee'),
            ]
            for doc in self.env['document.expiry'].search(domain):
                group = doc._get_expired_group()
                if not doc.employee_id.active:
                    continue
                for user in group.users:
                    self._create_activity(
                        doc, doc.employee_id, user, xml_id, state)
                if not doc.warn_employee:
                    continue
                employee_user = doc.employee_id.user_id
                if not employee_user:
                    continue
                self._create_activity(
                    doc, doc.employee_id, employee_user, xml_id, state)
