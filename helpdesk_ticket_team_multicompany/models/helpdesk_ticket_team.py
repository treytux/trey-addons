###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class HelpdeskTicketTeam(models.Model):
    _inherit = 'helpdesk.ticket.team'

    ALIAS_WRITEABLE_FIELDS = [
        'alias_name',
        'alias_contact',
        'alias_defaults',
        'alias_bounced_content',
        'mail_server_id',
    ]

    def _get_default_mail_server_id(self, company_id=None):
        company_id = company_id or self.env.company.id
        MailServer = self.env['ir.mail_server'].sudo()
        mail_server = MailServer.search([
            ('active', '=', True),
            ('company_id', '=', company_id)
        ], order='sequence, id', limit=1)
        return mail_server.id if mail_server else False

    def _resolve_alias_domain(self, vals):
        alias_domain = vals.pop('alias_domain', False)
        if not alias_domain:
            return False
        company_id = vals.get('company_id') or self.env.company.id
        mail_server_id = self.env['mail.alias']._get_server_from_alias_domain(
            alias_domain, company_id=company_id)
        vals['mail_server_id'] = mail_server_id
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            alias_domain_provided = self._resolve_alias_domain(vals)
            if not alias_domain_provided and not vals.get('mail_server_id'):
                vals['mail_server_id'] = self._get_default_mail_server_id(
                    vals.get('company_id'))
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        self._resolve_alias_domain(vals)
        return super().write(vals)
