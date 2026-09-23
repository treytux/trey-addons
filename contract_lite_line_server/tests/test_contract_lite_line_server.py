###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestContractLiteLineServer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_lang_installed('es_ES')

    @classmethod
    def _ensure_lang_installed(cls, code):
        lang_model = cls.env['res.lang'].with_context(active_test=False)
        lang = lang_model._activate_lang(code)
        if not lang:
            lang = lang_model._create_lang(code)
        mods = cls.env['ir.module.module'].search([
            ('state', '=', 'installed'),
        ])
        mods._update_translations([code], overwrite=True)
        return lang

    def setUp(self):
        super().setUp()
        self.today = fields.Date.context_today(self.env.user)
        self.partner = self.env['res.partner'].create({
            'name': 'Server Customer',
        })
        self.product = self.env['product.product'].create({
            'name': 'Managed Server',
            'type': 'service',
            'is_server': True,
        })
        self.other_product = self.env['product.product'].create({
            'name': 'Regular Service',
            'type': 'service',
        })
        self.contract = self.env['contract_lite.contract'].create({
            'name': 'Server Contract',
            'partner_id': self.partner.id,
            'company_id': self.env.company.id,
            'state': 'active',
        })

    def _create_line(self, product=None, **overrides):
        vals = {
            'contract_id': self.contract.id,
            'product_id': (product or self.product).id,
            'quantity': 1.0,
            'uom_id': (product or self.product).uom_id.id,
            'name': 'Managed server line',
            'recurring_interval': 1,
            'recurring_rule_type': 'monthly',
            'date_start': self.today,
            'recurring_next_date': self.today,
        }
        vals.update(overrides)
        return self.env['contract_lite.line'].create(vals)

    def _get_space_notification_template(self):
        return self.env.ref(
            'contract_lite_line_server.'
            'mail_template_contract_lite_line_server_space_usage',
        )

    def _set_space_notification_template(
            self, subject_en, body_en, subject_es=False, body_es=False):
        template = self._get_space_notification_template()
        template.write({
            'subject': subject_en,
            'body_html': body_en,
        })
        if subject_es or body_es:
            template.with_context(lang='es_ES').write({
                'subject': subject_es or subject_en,
                'body_html': body_es or body_en,
            })
        return template

    def test_server_product_sets_line_flag(self):
        line = self._create_line()
        self.assertTrue(line.is_product_server)
        regular_line = self._create_line(product=self.other_product)
        self.assertFalse(regular_line.is_product_server)

    def test_server_fields_can_be_stored(self):
        expansion = self._create_line(name='Disk expansion', quantity=50.0)
        line = self._create_line(
            server_name='server_name',
            container_name='container_name',
            contracted_space_gb=80.0,
            consumed_space_gb=97.0,
            disk_expansion_line_id=expansion.id,
        )
        self.assertEqual(line.server_name, 'server_name')
        self.assertEqual(line.container_name, 'container_name')
        self.assertEqual(line.contracted_space_gb, 80.0)
        self.assertEqual(line.consumed_space_gb, 97.0)
        self.assertEqual(line.disk_expansion_line_id, expansion)
        self.assertEqual(line.disk_expansion_space_gb, 50.0)
        self.assertEqual(line.current_space_balance_gb, 33.0)

    def test_suggested_expansion_uses_historical_growth_projection(self):
        expansion = self._create_line(name='Disk expansion', quantity=20.0)
        line = self._create_line(
            contracted_space_gb=80.0,
            consumed_space_gb=130.0,
            disk_expansion_line_id=expansion.id,
            date_start=self.today - timedelta(days=360),
        )
        self.assertEqual(line.suggested_expansion_gb, 120.0)

    def test_suggested_expansion_rounds_up_to_ten(self):
        line = self._create_line(
            contracted_space_gb=95.0,
            consumed_space_gb=80.0,
            date_start=self.today - timedelta(days=180),
        )
        self.assertEqual(line.current_space_balance_gb, 15.0)
        self.assertEqual(line.suggested_expansion_gb, 90.0)

    def test_suggested_expansion_uses_minimum_ten_when_positive(self):
        line = self._create_line(
            contracted_space_gb=100.0,
            consumed_space_gb=47.0,
            date_start=self.today - timedelta(days=180),
        )
        self.assertEqual(line.suggested_expansion_gb, 10.0)

    def test_current_space_balance_can_be_negative(self):
        line = self._create_line(
            contracted_space_gb=20.0,
            consumed_space_gb=45.0,
        )
        self.assertEqual(line.current_space_balance_gb, -25.0)

    def test_line_domain_finds_negative_server_balance(self):
        negative_line = self._create_line(
            contracted_space_gb=20.0,
            consumed_space_gb=45.0,
        )
        other_contract = self.env['contract_lite.contract'].create({
            'name': 'Other Server Contract',
            'partner_id': self.partner.id,
            'company_id': self.env.company.id,
            'state': 'active',
        })
        healthy_server_line = self._create_line(
            contract_id=other_contract.id,
            contracted_space_gb=50.0,
            consumed_space_gb=10.0,
        )
        regular_negative_line = self._create_line(
            contract_id=other_contract.id,
            product=self.other_product,
            contracted_space_gb=20.0,
            consumed_space_gb=40.0,
        )
        lines = self.env['contract_lite.line'].search([
            ('is_product_server', '=', True),
            ('current_space_balance_gb', '<', 0),
        ])
        self.assertIn(negative_line, lines)
        self.assertNotIn(healthy_server_line, lines)
        self.assertNotIn(regular_negative_line, lines)

    def test_parse_occupation_extracts_error_and_ok_lines(self):
        wizard = self.env[
            'contract.lite.line.server.occupation.import.wizard'].create({
                'customer_occupation': (
                    '[ INFO ] Leyendo información\n'
                    '[ ERROR ] container_name: 97G (~97.00G) de 80G '
                    '(Sin espacio)\n'
                    '[ OK ] healthy_container: 17G (~17.00G) de 20G\n'
                    '[WARNING] 1 contenedor(es) superan el espacio reservado.'
                ),
            })
        occupations, ignored_lines = wizard._parse_occupation()
        self.assertEqual(occupations, {
            'container_name': 97.0,
            'healthy_container': 17.0,
        })
        self.assertFalse(ignored_lines)

    def test_notify_server_space_usage_creates_notify_and_chatter_trace(self):
        commercial_follower = self.env['res.partner'].create({
            'name': 'Commercial Follower',
            'email': 'commercial@example.com',
        })
        contract_follower = self.env['res.partner'].create({
            'name': 'Contract Follower',
            'email': 'contract@example.com',
        })
        self.partner.commercial_partner_id.message_subscribe(
            partner_ids=commercial_follower.ids,
        )
        self.contract.message_subscribe(partner_ids=contract_follower.ids)
        self.env.company.partner_id.write({'lang': 'en_US'})
        self.env.user.write({'lang': 'en_US'})
        (commercial_follower | contract_follower).write({'lang': 'en_US'})
        self._set_space_notification_template(
            'Custom server space usage',
            '<p>Template marker for server space usage</p>',
        )
        line = self._create_line(
            contracted_space_gb=20.0,
            consumed_space_gb=45.0,
        )
        line.with_context(lang='en_US').action_notify_server_space_usage()
        traced_messages = self.contract.message_ids.filtered(
            lambda m: bool(m.body) and m.subtype_id == self.env.ref(
                'mail.mt_note')
        )
        self.assertTrue(traced_messages)
        notify_messages = self.env['mail.message'].search([
            ('model', '=', 'contract_lite.contract'),
            ('res_id', '=', self.contract.id),
            ('message_type', '=', 'user_notification'),
        ])
        self.assertTrue(notify_messages)
        notified_emails = set(
            notify_messages.notification_ids.mapped('res_partner_id.email')
        )
        self.assertIn('commercial@example.com', notified_emails)
        self.assertIn('contract@example.com', notified_emails)
        notify_bodies = ' '.join(notify_messages.mapped('body'))
        self.assertIn('Template marker for server space usage', notify_bodies)
        trace_bodies = ' '.join(traced_messages.mapped('body'))
        self.assertIn('Template marker for server space usage', trace_bodies)
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'contract_lite.contract'),
            ('res_id', '=', self.contract.id),
        ])
        self.assertFalse(activities)

    def test_notify_uses_partner_lang_for_email_and_company_for_wall(self):
        installed_langs = self.env['res.lang'].search([]).mapped('code')
        self.assertTrue(installed_langs)
        self.assertIn('es_ES', installed_langs)
        self.assertIn('en_US', installed_langs)
        company_lang = 'es_ES'
        self.env.company.partner_id.write({'lang': company_lang})
        self.partner.write({'lang': company_lang})
        follower_lang = 'en_US'
        follower_en = self.env['res.partner'].create({
            'name': 'Follower EN',
            'email': 'en@example.com',
            'lang': follower_lang,
        })
        follower_no_lang = self.env['res.partner'].create({
            'name': 'Follower without lang',
            'email': 'no-lang@example.com',
        })
        follower_no_lang.write({'lang': False})
        self.contract.message_subscribe(
            partner_ids=(follower_en | follower_no_lang).ids,
        )
        self._set_space_notification_template(
            'English server space usage',
            '<p>English template marker</p>',
            subject_es='Spanish server space usage',
            body_es='<p>Spanish template marker</p>',
        )
        self.env.user.write({'lang': 'en_US'})
        line = self._create_line(
            contracted_space_gb=20.0,
            consumed_space_gb=25.0,
        )
        line.action_notify_server_space_usage()
        wall_messages = self.contract.message_ids.filtered(
            lambda m: 'Spanish template marker' in (m.body or '')
        )
        self.assertTrue(wall_messages)
        wall_message = wall_messages.sorted('id')[-1]
        self.assertIn('Spanish template marker', wall_message.body)
        self.assertNotIn('English template marker', wall_message.body)
        notify_messages = self.env['mail.message'].search([
            ('model', '=', 'contract_lite.contract'),
            ('res_id', '=', self.contract.id),
            ('message_type', '=', 'user_notification'),
        ])
        self.assertTrue(notify_messages)
        notified_emails = set(
            notify_messages.notification_ids.mapped('res_partner_id.email')
        )
        self.assertIn('en@example.com', notified_emails)
        self.assertIn('no-lang@example.com', notified_emails)
        notify_bodies = ' '.join(notify_messages.mapped('body'))
        self.assertIn('English template marker', notify_bodies)
        self.assertIn('Spanish template marker', notify_bodies)

    def test_parse_occupation_accepts_decimal_comma(self):
        wizard = self.env[
            'contract.lite.line.server.occupation.import.wizard'].create({
                'customer_occupation': (
                    '[ ERROR ] container_name: 97,5G (~97.50G) de 80G '
                    '(Sin espacio)'
                ),
            })
        occupations, ignored_lines = wizard._parse_occupation()
        self.assertEqual(occupations, {'container_name': 97.5})
        self.assertFalse(ignored_lines)

    def test_apply_updates_all_matching_active_server_lines(self):
        container_name = 'container_name_%s' % self.contract.id
        line_01 = self._create_line(container_name=container_name)
        line_02 = self._create_line(container_name=container_name)
        self._create_line(
            product=self.other_product,
            container_name=container_name,
        )
        wizard = self.env[
            'contract.lite.line.server.occupation.import.wizard'].create({
                'customer_occupation': (
                    '[ ERROR ] %s: 97G (~97.00G) de 80G '
                    '(Sin espacio)' % container_name
                ),
            })
        wizard.with_context(
            active_model='contract_lite.contract',
            active_ids=self.contract.ids,
            lang='en_US',
        ).button_apply()
        wizard.button_apply_changes()
        self.assertEqual(line_01.consumed_space_gb, 97.0)
        self.assertEqual(line_02.consumed_space_gb, 97.0)
        self.assertIn('Updated lines: 2', wizard.result_summary)
        self.assertIn(container_name, wizard.result_summary)
        self.assertIn('97.0 GB (2 lines)', wizard.result_summary)

    def test_apply_updates_only_selected_contracts(self):
        container_name = 'shared_%s' % self.contract.id
        selected_line = self._create_line(container_name=container_name)
        other_contract = self.env['contract_lite.contract'].create({
            'name': 'Other Server Contract',
            'partner_id': self.partner.id,
            'company_id': self.env.company.id,
            'state': 'active',
        })
        other_line = self._create_line(
            contract_id=other_contract.id,
            container_name=container_name,
        )
        wizard = self.env[
            'contract.lite.line.server.occupation.import.wizard'].create({
                'customer_occupation': (
                    '[ ERROR ] %s: 33G (~33.00G) de 20G '
                    '(Sin espacio)' % container_name
                ),
            })
        wizard.with_context(
            active_model='contract_lite.contract',
            active_ids=self.contract.ids,
            lang='en_US',
        ).button_apply()
        wizard.button_apply_changes()
        self.assertEqual(selected_line.consumed_space_gb, 33.0)
        self.assertEqual(other_line.consumed_space_gb, 0.0)
        self.assertIn('Updated lines: 1', wizard.result_summary)
        self.assertIn(container_name, wizard.result_summary)

    def test_import_does_not_apply_until_apply_changes(self):
        line = self._create_line(container_name='missing')
        wizard = self.env[
            'contract.lite.line.server.occupation.import.wizard'].create({
                'customer_occupation': (
                    '[ ERROR ] missing: 12G (~12.00G) de 20G '
                    '(Sin espacio)'
                ),
            })
        wizard.with_context(
            active_model='contract_lite.contract',
            active_ids=self.contract.ids,
            lang='en_US',
        ).button_apply()
        self.assertEqual(line.consumed_space_gb, 0.0)
        self.assertTrue(wizard.import_payload)

    def test_apply_changes_closes_wizard(self):
        wizard = self.env[
            'contract.lite.line.server.occupation.import.wizard'].create({
                'customer_occupation': (
                    '[ ERROR ] missing: 12G (~12.00G) de 20G '
                    '(Sin espacio)'
                ),
            })
        wizard.with_context(lang='en_US').button_apply()
        result = wizard.button_apply_changes()
        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})

    def test_apply_reports_not_found_and_ignored_lines(self):
        wizard = self.env[
            'contract.lite.line.server.occupation.import.wizard'].create({
                'customer_occupation': (
                    '[ ERROR ] missing: 12G (~12.00G) de 20G '
                    '(Sin espacio)\n'
                    '[ ERROR ] bad line without usage'
                ),
            })
        wizard.with_context(lang='en_US').button_apply()
        self.assertIn('Containers not found: 1', wizard.result_summary)
        self.assertIn('- missing', wizard.result_summary)
        self.assertIn('Ignored error lines: 1', wizard.result_summary)
