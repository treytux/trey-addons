###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import random

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    barcode = fields.Char(
        string='Barcode',
        copy=False,
    )

    def get_registration_barcode(self):
        create_date_tz = fields.Datetime.context_timestamp(
            self.with_context(tz=self.event_id.date_tz),
            timestamp=self.create_date)
        random_nmbr = random.randint(1000, 9999)
        prefix = '%s%s' % (create_date_tz.strftime('%y%m%d%H%M'), random_nmbr)
        return '%s%s' % (prefix, self.id)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.barcode = res.get_registration_barcode()
        return res

    @api.constrains('barcode')
    def _check_barcode_registration_unique(self):
        for registration in self:
            if not registration.barcode:
                continue
            registration_count = self.env['event.registration'].search_count([
                ('barcode', '=', registration.barcode),
                ('id', '!=', registration.id),
                '|',
                ('company_id', '=', False),
                ('company_id', '=', registration.company_id.id),
            ])
            if registration_count:
                raise ValidationError(_(
                    'The barcode %s already exists in another ticket') % (
                    registration.barcode))
