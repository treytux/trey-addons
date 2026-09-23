###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class DocumentExpiry(models.Model):
    _inherit = 'document.expiry'

    owner_type = fields.Selection(
        selection_add=[('partner', 'Partner')]
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
    )

    @api.model
    def _get_expired_group(self):
        self.ensure_one()
        if self.owner_type == 'partner':
            return self.env.ref(
                'document_expiry_partner.document_partner_expiry_warn')
        return super()._get_expired_group()

    @api.model
    def _get_summary(self, state, owner_type):
        result = super()._get_summary(state, owner_type)
        if owner_type == 'partner':
            return _('Partner\'s documentation in state {}'.format(state.name))
        return result

    @api.model
    def document_expiry_warn_partner(self):
        Status = self.env['document.expiry.status']
        self._update_document_expiry_status()
        xml_id = 'document_expiry_partner.' \
                 'activity_document_expired_warn_partner'
        for state in Status.search([('warn', '=', True)]):
            domain = [
                ('status_id', '=', state.id),
                ('owner_type', '=', 'partner'),
            ]
            for doc in self.env['document.expiry'].search(domain):
                group = doc._get_expired_group()
                for user in group.users:
                    self._create_activity(
                        doc, doc.partner_id, user, xml_id, state)
