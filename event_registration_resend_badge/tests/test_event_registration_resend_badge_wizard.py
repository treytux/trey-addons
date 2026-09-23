###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.test_mail.tests.common import MockEmails
from odoo.exceptions import UserError
from odoo.tests import common
from psycopg2.errors import NotNullViolation


class TestEventRegistrationResendBadgeWizard(MockEmails, common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
        })
        self.company.partner_id.email = 'company@gmail.com'
        self.event = self.env['event.event'].create({
            'name': 'Test Conference',
            'date_begin': '2025-06-01 09:00:00',
            'date_end': '2025-06-03 18:00:00',
            'company_id': self.company.id,
        })
        self.attendee_1 = self.env['res.partner'].create({
            'name': 'Test Attendee One',
            'email': 'attendeeone@example.com',
        })
        self.attendee_confirmed_1 = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'Test Attendee Confirmed One',
            'email': self.attendee_1.email,
            'state': 'open',
            'partner_id': self.attendee_1.id,
        })
        self.attendee_2 = self.env['res.partner'].create({
            'name': 'Test Attendee Two',
            'email': 'attendeetwo@example.com',
        })
        self.attendee_confirmed_2 = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'Test Attendee Confirmed Two',
            'email': self.attendee_2.email,
            'state': 'open',
            'partner_id': self.attendee_2.id,
        })
        self.attendee_draft = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'Test Attendee Draft',
            'email': 'draft@example.com',
            'state': 'draft',
        })
        self.attendee_cancel = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'Test Attendee Cancel',
            'email': 'cancel@example.com',
            'state': 'cancel',
        })
        self.template = self.env['mail.template'].create({
            'name': 'Accreditation Template',
            'model_id': self.env.ref('event.model_event_registration').id,
            'subject': 'Accreditation for ${object.event_id.name}',
            'body_html': '<p>${object.name}</p><p>Accreditation attached.</p>',
            'attachment_ids': [(0, 0, {
                'name': 'accreditation.pdf',
            })],
        })

    def _open_wizard(self, selected_attendee_ids, template=None):
        wizard = self.env[
            'event.registration.resend.badge.wizard'].with_context(
            active_ids=selected_attendee_ids,
            active_model='event.registration'
        ).create({
            'template_id': (template or self.template).id,
        })
        if not wizard.attendee_ids:
            wizard.attendee_ids = [(6, 0, selected_attendee_ids)]
        return wizard

    def test_wizard_filters_only_confirmed_attendees_on_send(self):
        all_attendees = (
            self.attendee_confirmed_1 + self.attendee_confirmed_2
            + self.attendee_draft + self.attendee_cancel)

        self._open_wizard(all_attendees.ids).resend_accreditations()
        mails = self.env['mail.mail'].search([
            ('model', '=', 'event.registration'),
            ('res_id', 'in', [self.attendee_confirmed_1.id,
                              self.attendee_confirmed_2.id]),
        ])
        self.assertEqual(len(mails), 2)

    def test_wizard_requires_email_template(self):
        with self.assertRaises(NotNullViolation) as result:
            self.env['event.registration.resend.badge.wizard'].with_context(
                active_ids=[self.attendee_confirmed_1.id],
                active_model='event.registration'
            ).create({})
        self.assertIn('null', str(result.exception))
        self.assertIn('template_id', str(result.exception))

    def test_wizard_requires_at_least_one_confirmed_attendee(self):
        with self.assertRaises(UserError) as result:
            self._open_wizard([
                self.attendee_draft.id, self.attendee_cancel.id
            ]).resend_accreditations()
        self.assertIn(
            'No confirmed attendees in the selected records',
            str(result.exception))

    def test_email_attachment_generated(self):
        self._open_wizard([
            self.attendee_confirmed_1.id]).resend_accreditations()
        mail = self.env['mail.mail'].search([
            ('model', '=', 'event.registration'),
            ('res_id', '=', self.attendee_confirmed_1.id),
        ], limit=1)
        self.assertTrue(mail.attachment_ids)
        pdf_att = mail.attachment_ids.filtered(
            lambda a: a.mimetype == 'application/pdf'
            or a.name.endswith('.pdf')
        )
        self.assertTrue(pdf_att)

    def test_wizard_respects_selected_records_from_list_view(self):
        wizard = self.env[
            'event.registration.resend.badge.wizard'].with_context(
            active_ids=[self.attendee_confirmed_1.id, self.attendee_draft.id],
            active_model='event.registration'
        ).create({'template_id': self.template.id})
        self.assertEqual(len(wizard.attendee_ids), 2)
        self.assertIn(self.attendee_confirmed_1, wizard.attendee_ids)
        self.assertIn(self.attendee_draft, wizard.attendee_ids)

    def test_wizard_uses_selected_template_correctly(self):
        custom_template = self.env['mail.template'].create({
            'name': 'Test Accreditation',
            'model_id': self.env.ref('event.model_event_registration').id,
            'subject': self.attendee_confirmed_1.name,
            'body_html': '<p>Test Body</p>',
        })
        self._open_wizard(
            [self.attendee_confirmed_1.id],
            template=custom_template
        ).resend_accreditations()
        mail = self.env['mail.mail'].search([
            ('model', '=', 'event.registration'),
            ('res_id', '=', self.attendee_confirmed_1.id),
        ], limit=1)
        self.assertEqual(mail.subject, self.attendee_confirmed_1.name)
        self.assertIn('Test Body', mail.body_html)

    def test_wizard_prevents_sending_to_attendee_of_other_company(self):
        self.company_2 = self.env['res.company'].create({
            'name': 'Test Company Two',
        })
        self.company_2.partner_id.email = 'companytwo@gmail.com'
        test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user@test.com',
            'company_id': self.company_2.id,
            'company_ids': [(6, 0, [self.company_2.id])],
        })
        attendee_company2 = self.env['event.registration'].create({
            'event_id': self.event.id,
            'name': 'Attendee Company Two',
            'email': 'attendee_company2@example.com',
            'state': 'open',
            'company_id': self.company_2.id,
        })
        self.env = self.env(user=test_user)
        wizard = self.env['event.registration.resend.badge.wizard'].create({
            'attendee_ids': [(6, 0, [attendee_company2.id])],
            'template_id': self.template.id,
        })
        with self.assertRaises(UserError) as result:
            wizard.resend_accreditations()
        self.assertIn(
            'No confirmed attendees in the selected records',
            str(result.exception)
        )
