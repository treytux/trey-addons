##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from email.utils import formataddr, parseaddr

from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    mail_domain = fields.Char(
        string='Mail domain',
        help='Domain to be used in outgoing emails for this sales team.'
    )

    def _replace_email_domain(self, email_from, new_domain):
        name, email = parseaddr(email_from)
        if not email or '@' not in email:
            return email_from
        allow_domains = self.env['crm.team'].search([
            ('mail_domain', '!=', False),
        ]).mapped('mail_domain')
        if email.split('@')[1] not in allow_domains:
            return email_from
        local_part = email.split('@')[0]
        return formataddr((name, f"{local_part}@{new_domain}"))
