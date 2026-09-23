###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestHelpdeskTicketTeamMulticompany(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_param(
            'mail.catchall.domain', 'global.example.com'
        )
        self.other_company = self.env['res.company'].create({
            'name': 'Other company',
        })
        self.server_domain = self.env['ir.mail_server'].create({
            'name': 'Support server by domain',
            'smtp_host': 'smtp.domain.example',
            'smtp_user': 'mailer@domain.example',
            'from_filter': 'domain.example',
        })
        self.server_email = self.env['ir.mail_server'].create({
            'name': 'Support server by email',
            'smtp_host': 'smtp.email.example',
            'smtp_user': 'alerts@email.example',
            'from_filter': 'alerts@email.example',
        })
        self.server_smtp_user = self.env['ir.mail_server'].create({
            'name': 'Support server by smtp user',
            'smtp_host': 'smtp.user.example',
            'smtp_user': 'postmaster@user.example',
        })
        self.company_server = self.env['ir.mail_server'].create({
            'name': 'Company specific server',
            'smtp_host': 'smtp.company.example',
            'smtp_user': 'support@company.example',
            'from_filter': 'company.example',
            'company_id': self.other_company.id,
        })

    def test_helpdesk_team_alias_domain_uses_selected_mail_server(self):
        team = self.env['helpdesk.ticket.team'].create({
            'name': 'Support',
            'alias_name': 'support',
            'alias_domain': 'domain.example',
        })
        self.assertEqual(team.mail_server_id, self.server_domain)
        self.assertEqual(team.alias_domain, 'domain.example')
        self.assertEqual(team.alias_id.alias_domain, 'domain.example')
        self.assertEqual(team.alias_id.display_name, 'support@domain.example')
        team.write({'alias_domain': 'email.example'})
        self.env.invalidate_all()
        alias = self.env['mail.alias'].browse(team.alias_id.id)
        self.assertEqual(team.mail_server_id, self.server_email)
        self.assertEqual(team.alias_domain, 'email.example')
        self.assertEqual(alias.alias_domain, 'email.example')
        self.assertEqual(alias.display_name, 'support@email.example')

    def test_helpdesk_team_alias_domain_falls_back_to_catchall(self):
        team = self.env['helpdesk.ticket.team'].create({
            'name': 'Support',
            'alias_name': 'support-global',
        })
        self.assertFalse(team.mail_server_id)
        self.assertEqual(team.alias_domain, 'global.example.com')
        self.assertEqual(
            team.alias_id.display_name, 'support-global@global.example.com')

    def test_helpdesk_team_alias_domain_can_follow_email_from_filter(self):
        team = self.env['helpdesk.ticket.team'].create({
            'name': 'Support Email',
            'alias_name': 'support-email',
            'alias_domain': 'email.example',
        })
        self.assertEqual(team.alias_domain, 'email.example')
        self.assertEqual(
            team.alias_id.display_name, 'support-email@email.example')

    def test_helpdesk_team_alias_domain_can_follow_smtp_user_domain(self):
        team = self.env['helpdesk.ticket.team'].create({
            'name': 'Support SMTP User',
            'alias_name': 'support-smtp',
            'alias_domain': 'user.example',
        })
        self.assertEqual(team.alias_domain, 'user.example')
        self.assertEqual(
            team.alias_id.display_name, 'support-smtp@user.example')

    def test_helpdesk_team_default_mail_server_uses_company_server(self):
        team = self.env['helpdesk.ticket.team'].create({
            'name': 'Company support',
            'alias_name': 'company-support',
            'company_id': self.other_company.id,
        })
        self.assertEqual(team.mail_server_id, self.company_server)
        self.assertEqual(team.alias_domain, 'company.example')
        self.assertEqual(
            team.alias_id.display_name, 'company-support@company.example')

    def test_alias_domain_selection_uses_literal_catchall_domain(self):
        selection = dict(self.env['mail.alias']._selection_alias_domain())
        self.assertIn('global.example.com', selection)
        self.assertEqual(selection['global.example.com'], 'global.example.com')
