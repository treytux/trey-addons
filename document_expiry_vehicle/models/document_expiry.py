###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class DocumentExpiry(models.Model):
    _inherit = 'document.expiry'

    owner_type = fields.Selection(
        selection_add=[('vehicle', 'Vehicle')],
    )
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
    )

    @api.model
    def _get_expired_group(self):
        self.ensure_one()
        if self.owner_type == 'vehicle':
            return self.env.ref(
                'document_expiry_vehicle.document_vehicle_expiry_warn')
        return super()._get_expired_group()

    @api.model
    def _get_summary(self, state, owner_type):
        result = super()._get_summary(state, owner_type)
        if owner_type == 'vehicle':
            return _(
                'Vehicle\'s documentation in state {}'.format(state.name))
        return result

    @api.model
    def document_expiry_warn_vehicle(self):
        Status = self.env['document.expiry.status']
        self._update_document_expiry_status()
        xml_id = 'document_expiry_vehicle.' \
                 'activity_document_expired_warn_vehicle'
        for state in Status.search([('warn', '=', True)]):
            domain = [
                ('status_id', '=', state.id),
                ('owner_type', '=', 'vehicle'),
            ]
            for doc in self.env['document.expiry'].search(domain):
                group = doc._get_expired_group()
                for user in group.users:
                    self._create_activity(
                        doc, doc.vehicle_id, user, xml_id, state)

    @api.model
    def _get_selection_values(self):
        return [
            ('insurance', _('Insurance Policy')),
            ('guarantee', _('Manufacturer\'s Guarantee')),
            ('warranty', _('Workshop Warranty')),
            ('refueling', _('Refueling Cards')),
        ]

    @api.model
    def _selection_document_type(self):
        result = super()._selection_document_type()
        for value in self._get_selection_values():
            if value not in result:
                result.append(value)
        return result
