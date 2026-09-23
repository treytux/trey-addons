from unittest.mock import PropertyMock, patch

from odoo.tests.common import TransactionCase


class TestMailThread(TransactionCase):

    def setUp(self):
        super().setUp()
        self.record = self.env['res.partner'].create({
            'name': 'Test Record',
        })

    def test_sale_order_uses_type_name_if_no_model_description(self):
        record_class = type(self.record)
        with patch.object(record_class,
                          '_name',
                          new_callable=PropertyMock,
                          return_value='sale.order'), \
             patch.object(record_class,
                          'type_name',
                          new_callable=PropertyMock,
                          return_value='Sales Order',
                          create=True), \
             patch('odoo.addons.mail.models.mail_thread.MailThread.'
                   '_notify_thread_by_email',
                   autospec=True) as mock_super:
            self.record._notify_thread_by_email(
                message=None,
                recipients_data=[],
            )
            _, kwargs = mock_super.call_args
            model_description = kwargs.get('model_description')
            self.assertEqual(model_description, 'Sales Order')

    def test_sale_order_does_not_override_model_description(self):
        record_class = type(self.record)
        with patch.object(record_class,
                          '_name',
                          new_callable=PropertyMock,
                          return_value='sale.order'), \
             patch.object(record_class,
                          'type_name',
                          new_callable=PropertyMock,
                          return_value='Sales Order',
                          create=True), \
             patch('odoo.addons.mail.models.mail_thread.MailThread.'
                   '_notify_thread_by_email', autospec=True) as mock_super:
            self.record._notify_thread_by_email(
                message=None,
                recipients_data=[],
                model_description='Custom Description',
            )
            _, kwargs = mock_super.call_args
            model_description = kwargs.get('model_description')
            self.assertEqual(model_description, 'Custom Description')

    def test_other_model_not_affected(self):
        with patch('odoo.addons.mail.models.mail_thread.MailThread.'
                   '_notify_thread_by_email',
                   autospec=True) as mock_super:
            self.record._notify_thread_by_email(
                message=None,
                recipients_data=[],
            )
            _, kwargs = mock_super.call_args
            model_description = kwargs.get('model_description')
            self.assertFalse(model_description)
