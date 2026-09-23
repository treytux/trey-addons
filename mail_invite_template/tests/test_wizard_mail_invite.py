###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import MissingError
from odoo.tests import common


class TestWizardMailInviteTemplate(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner Invite Template Test',
        })

    def _default_get(self, fields_list, **ctx):
        return self.env['mail.wizard.invite'].with_context(**ctx).default_get(
            fields_list)

    def _message_text(self, values):
        message = values.get('message')
        if isinstance(message, bytes):
            return message.decode('utf-8')
        return message or ''

    def test_default_get_sets_message_when_message_in_fields(self):
        values = self._default_get(
            ['message', 'res_model', 'res_id'], default_res_model='res.partner',
            default_res_id=self.partner.id)
        self.assertIn('message', values)
        self.assertTrue(self._message_text(values))

    def test_default_get_uses_res_model_and_res_id_to_render_template(self):
        values = self._default_get(
            ['message', 'res_model', 'res_id'], default_res_model='res.partner',
            default_res_id=self.partner.id)
        self.assertIn('message', values)
        self.assertIn(self.partner.name, self._message_text(values))

    def test_default_get_does_not_crash_without_message_in_fields(self):
        values = self._default_get(
            ['res_model', 'res_id'], default_res_model='res.partner',
            default_res_id=self.partner.id)
        self.assertNotIn('message', values)

    def test_default_get_does_not_fill_message_without_res_model(self):
        values = self._default_get(
            ['message', 'res_id'], default_res_id=self.partner.id)
        self.assertNotIn('res_model', values)
        self.assertIn('message', values)
        self.assertNotIn(self.partner.name, self._message_text(values))

    def test_default_get_does_not_fill_message_without_res_id(self):
        values = self._default_get(
            ['message', 'res_model'], default_res_model='res.partner')
        self.assertEqual(values.get('res_model'), 'res.partner')
        self.assertFalse(values.get('res_id'))
        self.assertIn('message', values)
        self.assertNotIn(self.partner.name, self._message_text(values))

    def test_default_get_raises_missing_error_with_invalid_res_id(self):
        with self.assertRaises(MissingError):
            self._default_get(
                ['message', 'res_model', 'res_id'],
                default_res_model='res.partner', default_res_id=99999999)
