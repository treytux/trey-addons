###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models
from odoo.tools import email_domain_extract, email_domain_normalize


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    def _get_alias_domain(self):
        self.ensure_one()
        source = self.from_filter or self.smtp_user
        if not source:
            return False
        if '@' in source:
            return email_domain_extract(source)
        return email_domain_normalize(source)
