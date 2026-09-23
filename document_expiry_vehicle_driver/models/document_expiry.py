###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################

from odoo import _, api, fields, models


class DocumentExpiry(models.Model):
    _inherit = 'document.expiry'

    owner_type = fields.Selection(
        selection_add=[('driver', 'Driver')],
    )
    driver_id = fields.Many2one(
        comodel_name='res.partner',
        domain=lambda self: [("id", "in", self._domain_drivers().ids)],
    )
    document_type_driver = fields.Selection(
        selection=[
            ('custom', _('Custom')),
            ('attachment', _('Attachment')),
            ('community', _('Community License')),
            ('transportation', _('Transportation Card')),
            ('london', _('London License')),
        ],
        default='custom',
        required=True,
    )

    @api.model
    def _domain_drivers(self):
        return self.env['fleet.vehicle'].search([]).mapped('driver_id')

    @api.model
    def _get_expired_group(self):
        self.ensure_one()
        if self.owner_type == 'driver':
            return self.env.ref(
                'document_expiry_vehicle_driver.document_driver_expiry_warn')
        return super()._get_expired_group()

    @api.model
    def _get_summary(self, state, owner_type):
        result = super()._get_summary(state, owner_type)
        if owner_type == 'driver':
            return _('Driver\'s documentation in state {}'.format(state.name))
        return result

    @api.model
    def document_expiry_warn_driver(self):
        Status = self.env['document.expiry.status']
        self._update_document_expiry_status()
        xml_id = 'document_expiry_vehicle_driver.' \
                 'activity_document_expired_warn_driver'
        for state in Status.search([('warn', '=', True)]):
            domain = [
                ('status_id', '=', state.id),
                ('owner_type', '=', 'driver'),
            ]
            for doc in self.env['document.expiry'].search(domain):
                group = doc._get_expired_group()
                for user in group.users:
                    self._create_activity(
                        doc, doc.driver_id, user, xml_id, state)
