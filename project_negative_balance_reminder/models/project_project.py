###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from collections import defaultdict

from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    last_notification_date = fields.Date(
        string='Last notification date',
        help='Date of the last notification sent for negative balance',
        readonly=True,
        copy=False,
    )
    renewal_period_days = fields.Integer(
        string='Renewal period (days)',
        help='Number of days to wait before sending another notification',
        default=30,
    )

    def check_and_notify_negative_balance(self):
        today = fields.Date.today()
        domain = self._get_notify_candidates_domain()
        projects = self.search(domain)
        projects = projects.filtered(
            lambda project: project._has_negative_balance())
        for project in projects:
            if project._should_notify(today):
                project._send_negative_balance_email()
                project.last_notification_date = today

    def _get_notify_candidates_domain(self):
        domain = []
        fields_map = self._fields
        if 'active' in fields_map:
            domain.append(('active', '=', True))
        if 'is_template' in fields_map:
            domain.append(('is_template', '=', False))
        if 'allow_timesheets' in fields_map:
            domain.append(('allow_timesheets', '=', True))
        if 'contract_lite_line_id' in fields_map:
            domain.append(('contract_lite_line_id', '!=', False))
            domain.append(
                ('contract_lite_line_id.product_id.is_maintenance', '=', True)
            )
        return domain

    def _has_negative_balance(self):
        return self.current_balance < 0

    def _should_notify(self, today):
        return (
            not self.last_notification_date
            or (today - self.last_notification_date).days
            >= self.renewal_period_days)

    def _get_negative_balance_template(self):
        return self.env.ref(
            'project_negative_balance_reminder.email_template_negative_balance',
            raise_if_not_found=False,
        )

    def _get_valid_notification_lang(self, candidate_langs, fallback='es_ES'):
        self.ensure_one()
        for lang in candidate_langs:
            if not lang:
                continue
            if self.env['res.lang'].search_count([('code', '=', lang)]):
                return lang
        if self.env['res.lang'].search_count([('code', '=', fallback)]):
            return fallback
        installed_lang = self.env['res.lang'].search([], limit=1)
        if installed_lang:
            return installed_lang.code
        return fallback

    def _get_company_notification_lang(self):
        self.ensure_one()
        return self._get_valid_notification_lang([
            self.env.company.partner_id.lang,
            self.env.user.lang,
            'es_ES',
        ])

    def _get_partner_notification_lang(self, partner, default_lang):
        self.ensure_one()
        user_lang = partner.user_ids.sorted('id')[:1].lang
        return self._get_valid_notification_lang([
            user_lang,
            partner.lang,
            default_lang,
            'es_ES',
        ])

    def _render_negative_balance_notification_values(self, lang):
        self.ensure_one()
        template = self._get_negative_balance_template()
        if not template:
            return {}
        rendered = template.with_context(
            lang=lang, template_preview_lang=lang).generate_email(
            self.id, ['subject', 'body_html'])
        if 'body_html' in rendered:
            return rendered
        return rendered.get(self.id, {})

    def _send_negative_balance_email(self):
        self.ensure_one()
        partners = self.message_follower_ids.mapped(
            'partner_id').filtered('email')
        if not partners:
            return
        company_lang = self._get_company_notification_lang()
        partner_lang_map = defaultdict(list)
        for partner in partners:
            partner_lang = self._get_partner_notification_lang(
                partner, company_lang)
            partner_lang_map[partner_lang].append(partner.id)
        company_values = self._render_negative_balance_notification_values(
            company_lang)
        subject = company_values.get('subject')
        body_html = company_values.get('body_html')
        if body_html:
            self.message_post(
                subject=subject,
                body=body_html,
                subtype_xmlid='mail.mt_note',
            )
        for partner_lang in sorted(partner_lang_map):
            partner_ids = partner_lang_map[partner_lang]
            partner_values = self._render_negative_balance_notification_values(
                partner_lang
            )
            partner_subject = partner_values.get('subject')
            partner_body_html = partner_values.get('body_html')
            if not partner_body_html:
                continue
            self.message_notify(
                partner_ids=partner_ids,
                subject=partner_subject,
                body=partner_body_html,
                model='project.project',
                res_id=self.id,
            )
