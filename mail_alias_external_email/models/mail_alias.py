###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MailAlias(models.Model):
    _inherit = 'mail.alias'

    external_email = fields.Char(
        string='External email',
    )

    @api.constrains('external_email')
    def _check_external_email(self):
        for alias in self:
            if alias.external_email:
                match = re.match(
                    r'[\w.+-]+@[\w-]+\.[\w.-]+', alias.external_email)
                if match is None:
                    raise ValidationError(_('Not a valid email'))
