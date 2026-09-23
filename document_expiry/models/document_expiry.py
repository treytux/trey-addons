###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DocumentExpiry(models.Model):
    _name = 'document.expiry'
    _inherit = [
        'document.expiry.abstract', 'mail.thread', 'mail.activity.mixin']
    _description = 'Document Expiry'

    status_id = fields.Many2one(
        compute='_compute_status',
        store=True,
    )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for document in self:
            if document.end_date < document.start_date:
                raise ValidationError(
                    _('Expiry date cannot occur earlier than the start date.')
                )

    @api.depends('end_date', 'start_date')
    def _compute_status(self):
        states = self.env['document.expiry.status'].search(
            [], order='days asc')
        for document in self:
            if not document.end_date or not document.start_date:
                continue
            for state in states.filtered(
                    lambda s: not s.owner_type
                    or s.owner_type == document.owner_type):
                warn_date = fields.date.today() + timedelta(days=state.days)
                if fields.date.today() <= document.end_date <= warn_date:
                    document.status_id = state.id
                    break
                elif document.end_date > warn_date:
                    document.status_id = self.env.ref(
                        'document_expiry.document_expiry_status_valid').id
                elif document.end_date < fields.date.today():
                    document.status_id = self.env.ref(
                        'document_expiry.document_expiry_status_expired').id

    @api.model
    def _get_expired_group(self):
        self.ensure_one()
        return self.env.ref('document_expiry.document_generic_expiry_warn')

    @api.model
    def _update_document_expiry_status(self):
        self.search([])._compute_status()

    @api.model
    def _get_summary(self, state, owner_type):
        if owner_type == 'other':
            return _('Document in state {}.'.format(state.name))
        return ''

    @api.model
    def _create_activity(self, doc, model, user, xml_id, state):
        activity_type = self.env.ref(xml_id)
        summary = self._get_summary(state, doc.owner_type)
        doc_users = model.activity_ids.filtered(
            lambda x: x.activity_type_id == activity_type).mapped(
            'user_id')
        if user not in doc_users:
            model.activity_schedule(
                summary=summary,
                act_type_xmlid=xml_id,
                date_deadline=fields.Date.today(),
                user_id=user.id,
            )

    @api.model
    def document_expiry_warn(self):
        Status = self.env['document.expiry.status']
        self._update_document_expiry_status()
        xml_id = 'document_expiry.activity_document_expired_warn'
        for state in Status.search([('warn', '=', True)]):
            domain = [
                ('status_id', '=', state.id),
                ('owner_type', '=', 'other'),
            ]
            for doc in self.env['document.expiry'].search(domain):
                group = doc._get_expired_group()
                for user in group.users:
                    self._create_activity(doc, doc, user, xml_id, state)
