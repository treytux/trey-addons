###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################

from odoo import _, api, fields, models


class DocumentExpiry(models.Model):
    _inherit = 'document.expiry'

    inspection_id = fields.Many2one(
        comodel_name='fleet.vehicle.inspection',
    )
    inspection_needed = fields.Boolean(
        compute='_compute_inspection_needed',
    )

    @api.model
    def _get_selection_values(self):
        values = super()._get_selection_values()
        values += [
            ('itv', _('ITV')),
            ('tachograph', _('Tachograph')),
            ('extinguishers', _('Extinguishers')),
            ('oil', _('Oil')),
            ('filters', _('Filters')),
            ('brakes', _('Brakes')),
        ]
        return values

    @api.depends('document_type')
    def _compute_inspection_needed(self):
        for doc in self:
            doc.inspection_needed = doc.document_type in [
                'itv', 'tachograph', 'extinguishers', 'oil', 'filters',
                'brakes']

    @api.model
    def _selection_document_type(self):
        result = super()._selection_document_type()
        for value in self._get_selection_values():
            if self.env.context.get('default_owner_type', False) == 'vehicle' \
                    and value not in result:
                result.append(value)
        return result
