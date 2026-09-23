###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import math
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ContractLiteLine(models.Model):
    _inherit = 'contract_lite.line'

    is_product_server = fields.Boolean(
        string='Is server',
        compute='_compute_is_product_server',
        store=True,
    )
    server_name = fields.Char(
        string='Server',
    )
    container_name = fields.Char(
        string='Container',
    )
    contracted_space_gb = fields.Float(
        string='Contracted space (GB)',
    )
    consumed_space_gb = fields.Float(
        string='Consumed space (GB)',
    )
    disk_expansion_line_id = fields.Many2one(
        comodel_name='contract_lite.line',
        string='Disk expansion',
    )
    disk_expansion_space_gb = fields.Float(
        string='Expanded space (GB)',
        related='disk_expansion_line_id.quantity',
        readonly=True,
    )
    suggested_expansion_gb = fields.Float(
        string='Suggested expansion (GB)',
        compute='_compute_suggested_expansion_gb',
    )
    current_space_balance_gb = fields.Float(
        string='Current space balance (GB)',
        compute='_compute_current_space_balance_gb',
        store=True,
    )

    @api.depends('product_id', 'product_id.is_server')
    def _compute_is_product_server(self):
        for line in self:
            line.is_product_server = (
                line.product_id.is_server if line.product_id else False)

    @api.depends(
        'date_start',
        'contracted_space_gb',
        'consumed_space_gb',
        'contract_id',
        'disk_expansion_space_gb',
    )
    def _compute_suggested_expansion_gb(self):
        today = fields.Date.context_today(self)
        for line in self:
            current_capacity = (
                (line.contracted_space_gb or 0.0)
                + (line.disk_expansion_space_gb or 0.0))
            consumed_space = line.consumed_space_gb or 0.0
            start_date = getattr(line.contract_id, 'date_start', False)
            start_date = start_date or line.date_start or today
            days_elapsed = max((today - start_date).days, 0)
            months_elapsed = max(1.0, days_elapsed / 30.0)
            monthly_growth = consumed_space / months_elapsed
            projected_growth = monthly_growth * 6.0
            future_required = consumed_space + projected_growth
            future_required_with_buffer = future_required * 1.10
            suggested_space = future_required_with_buffer - current_capacity
            suggested_space = max(suggested_space, 0.0)
            if suggested_space:
                line.suggested_expansion_gb = (
                    math.ceil(suggested_space / 10.0) * 10.0)
            else:
                line.suggested_expansion_gb = 0.0

    @api.depends(
        'contracted_space_gb',
        'consumed_space_gb',
        'disk_expansion_space_gb',
    )
    def _compute_current_space_balance_gb(self):
        for line in self:
            available_space = (
                (line.contracted_space_gb or 0.0)
                + (line.disk_expansion_space_gb or 0.0))
            consumed_space = line.consumed_space_gb or 0.0
            line.current_space_balance_gb = available_space - consumed_space

    def _get_space_notification_template(self):
        return self.env.ref(
            'contract_lite_line_server.'
            'mail_template_contract_lite_line_server_space_usage',
            raise_if_not_found=False,
        )

    def action_open_space_notification_template(self):
        template = self._get_space_notification_template()
        if not template:
            raise UserError(_(
                'The server space usage email template is missing.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Server space usage notification'),
            'res_model': 'mail.template',
            'view_mode': 'form',
            'target': 'current',
            'res_id': template.id,
        }

    def _get_notification_partners(self):
        self.ensure_one()
        commercial_partner = self.contract_id.partner_id.commercial_partner_id
        return (
            commercial_partner.message_partner_ids
            | self.contract_id.message_partner_ids).filtered('email')

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

    def _render_space_notification_template(self, template, fields_list, lang):
        self.ensure_one()
        rendered = template.with_context(
            lang=lang, template_preview_lang=lang).generate_email(
            self.id, fields_list)
        if 'body_html' in rendered:
            return rendered
        return rendered.get(self.id, {})

    def action_notify_server_space_usage(self):
        server_lines = self.filtered('is_product_server')
        if not server_lines:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Server notifications'),
                    'message': _(
                        'No server lines were selected for notification.'
                    ),
                    'type': 'warning',
                    'sticky': False,
                },
            }
        template = self._get_space_notification_template()
        if not template:
            raise UserError(_(
                'The server space usage email template is missing.'))
        fields_list = ['subject', 'body_html']
        mailed_lines = 0
        for line in server_lines:
            company_lang = line._get_company_notification_lang()
            partners = line._get_notification_partners()
            partner_lang_map = defaultdict(list)
            for partner in partners:
                partner_lang = line._get_partner_notification_lang(
                    partner, company_lang)
                partner_lang_map[partner_lang].append(partner.id)
            values = line._render_space_notification_template(
                template, fields_list, company_lang)
            subject = values.get(
                'subject', _('Server space usage notification'))
            message_html = values.get('body_html')
            if message_html:
                line.contract_id.message_post(
                    subject=subject,
                    body=message_html,
                    subtype_xmlid='mail.mt_note',
                )
            for partner_lang in sorted(partner_lang_map):
                partner_ids = partner_lang_map[partner_lang]
                partner_values = line._render_space_notification_template(
                    template, fields_list, partner_lang)
                partner_subject = partner_values.get(
                    'subject', _('Server space usage notification'))
                partner_message_html = partner_values.get('body_html')
                if not partner_message_html:
                    continue
                line.contract_id.message_notify(
                    partner_ids=partner_ids,
                    subject=partner_subject,
                    body=partner_message_html,
                    model='contract_lite.contract',
                    res_id=line.contract_id.id,
                )
            if partner_lang_map:
                mailed_lines += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Server notifications'),
                'message': _(
                    'Processed %(processed)s line(s). '
                    'Email created for %(mailed)s line(s).'
                ) % {
                    'processed': len(server_lines),
                    'mailed': mailed_lines,
                },
                'type': 'success',
                'sticky': False,
            },
        }
