###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class MailAlias(models.Model):
    _inherit = 'mail.alias'

    mail_server_id = fields.Many2one(
        comodel_name='ir.mail_server',
        string='Mail server',
        help=(
            'Mail server used to derive the alias domain. '
            'When it is empty, the global catchall domain is used.'
        ),
    )
    alias_domain = fields.Selection(
        selection='_selection_alias_domain',
        compute='_compute_alias_domain',
        inverse='_inverse_alias_domain',
        string='Alias domain',
    )

    @api.model
    def _selection_alias_domain(self):
        selection = []
        domains_seen = set()
        mail_servers = self.env['ir.mail_server'].sudo().search([
            ('active', '=', True),
        ], order='sequence, id')
        for mail_server in mail_servers:
            alias_domain = mail_server._get_alias_domain()
            if not alias_domain or alias_domain in domains_seen:
                continue
            label = mail_server.display_name
            if mail_server.company_id:
                label = '%s (%s)' % (
                    label, mail_server.company_id.display_name)
            selection.append((alias_domain, label))
            domains_seen.add(alias_domain)
        current_mail_server = self[:1].mail_server_id if self else False
        if current_mail_server:
            alias_domain = current_mail_server._get_alias_domain()
            if alias_domain and alias_domain not in domains_seen:
                label = current_mail_server.display_name
                if not current_mail_server.active:
                    label = '%s (%s)' % (label, _('inactive'))
                selection.append((alias_domain, label))
                domains_seen.add(alias_domain)
        catchall_domain = self.env['ir.config_parameter'].sudo().get_param(
            'mail.catchall.domain')
        if catchall_domain and catchall_domain not in domains_seen:
            selection.append((catchall_domain, catchall_domain))
        return selection

    @api.depends(
        'alias_name',
        'mail_server_id',
        'mail_server_id.from_filter',
        'mail_server_id.smtp_user',
    )
    def _compute_alias_domain(self):
        catchall_domain = self.env['ir.config_parameter'].sudo().get_param(
            'mail.catchall.domain')
        for alias in self:
            alias_domain = (
                alias.mail_server_id._get_alias_domain()
                if alias.mail_server_id
                else False)
            alias.alias_domain = alias_domain or catchall_domain

    def _inverse_alias_domain(self):
        for alias in self:
            alias.mail_server_id = alias._get_server_from_alias_domain(
                alias.alias_domain,
                company_id=(
                    alias.company_id.id
                    if 'company_id' in alias._fields and alias.company_id
                    else False))

    def _get_server_from_alias_domain(self, alias_domain, company_id=False):
        if not alias_domain:
            return False
        mail_servers = self.env['ir.mail_server'].sudo().search([
            ('active', '=', True),
        ], order='sequence, id')
        if company_id:
            company_mail_servers = mail_servers.filtered(
                lambda server: not server.company_id
                or server.company_id.id == company_id)
            matching_mail_servers = company_mail_servers.filtered(
                lambda server: server._get_alias_domain() == alias_domain)
            if matching_mail_servers:
                return matching_mail_servers[0].id
        matching_mail_servers = mail_servers.filtered(
            lambda server: server._get_alias_domain() == alias_domain)
        if matching_mail_servers:
            return matching_mail_servers[0].id
        return False
