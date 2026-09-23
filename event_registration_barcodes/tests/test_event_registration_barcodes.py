###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import _, exceptions
from odoo.tests import common


class TestEventRegistrationBarcodes(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.partner_main_location = self.env['res.partner'].create({
            'name': 'Main location',
        })
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        date_end = datetime.now() + relativedelta(days=3)
        self.event = self.env['event.event'].create({
            'name': 'Test event',
            'date_begin': today,
            'date_end': date_end.strftime('%Y-%m-%d %H:%M:%S'),
            'address_id': self.partner_main_location.id,
        })
        self.registration = self.env['event.registration'].create({
            'event_id': self.event.id,
            'partner_id': self.partner.id,
        })

    def test_validate_event_registration_ok_01(self):
        self.assertEqual(self.event.state, 'draft')
        self.event.button_confirm()
        self.assertEqual(self.event.state, 'confirm')
        self.assertEqual(self.registration.state, 'draft')
        self.registration.confirm_registration()
        self.assertEqual(self.registration.state, 'open')
        self.assertTrue(self.registration.barcode)
        wizard = self.env['event.registration.barcodes'].create({
            'event_id': self.event.id,
        })
        wizard._origin = wizard
        self.assertTrue(wizard.event_id)
        self.assertEqual(wizard.event_id, self.event)
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        wizard.read_event_ticket(self.registration.barcode)
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 1)
        self.assertEqual(self.registration.state, 'done')
        wizard_line = wizard.with_context(wizard_id=wizard.id).line_ids[0]
        self.assertEqual(wizard_line.wizard_id, wizard)
        self.assertEqual(wizard_line.name, self.registration.name)
        self.assertEqual(wizard_line.barcode, self.registration.barcode)
        self.assertEqual(
            wizard.message, _('Ticket successfully validated'))
        self.assertEqual(wizard.message_type, 'success')

    def test_registration_not_in_event_error_02(self):
        self.assertEqual(self.event.state, 'draft')
        self.event.button_confirm()
        self.assertEqual(self.event.state, 'confirm')
        self.assertEqual(self.registration.state, 'draft')
        self.registration.confirm_registration()
        self.assertEqual(self.registration.state, 'open')
        self.assertTrue(self.registration.barcode)
        wizard = self.env['event.registration.barcodes'].create({
            'event_id': self.event.id,
        })
        wizard._origin = wizard
        event_02 = self.env['event.event'].create({
            'name': 'Test event 2',
            'date_begin': datetime.now(),
            'date_end': datetime.now() + relativedelta(days=5),
        })
        registration_02 = self.env['event.registration'].create({
            'event_id': event_02.id,
            'partner_id': self.partner.id,
        })
        self.assertEqual(registration_02.event_id, event_02)
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        wizard.read_event_ticket(registration_02.barcode)
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        self.assertEqual(wizard.message_type, 'other_event')
        self.assertEqual(
            wizard.message, _('Ticket does not belong to this event'))

    def test_registration_barcode_not_found_03(self):
        self.assertEqual(self.event.state, 'draft')
        self.event.button_confirm()
        self.assertEqual(self.event.state, 'confirm')
        self.assertEqual(self.registration.state, 'draft')
        self.registration.confirm_registration()
        self.assertEqual(self.registration.state, 'open')
        wizard = self.env['event.registration.barcodes'].create({
            'event_id': self.event.id,
        })
        wizard._origin = wizard
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        wizard.read_event_ticket('123456789')
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        self.assertEqual(wizard.message_type, 'error')
        self.assertEqual(wizard.message, _('Ticket not found'))

    def test_validate_registration_not_confirmed_04(self):
        self.assertEqual(self.event.state, 'draft')
        self.event.button_confirm()
        self.assertEqual(self.event.state, 'confirm')
        self.assertEqual(self.registration.state, 'draft')
        wizard = self.env['event.registration.barcodes'].create({
            'event_id': self.event.id,
        })
        wizard._origin = wizard
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        wizard.read_event_ticket(self.registration.barcode)
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        self.assertEqual(wizard.message_type, 'not_confirmed')
        self.assertEqual(wizard.message, _('Ticket not confirmed'))

    def test_registration_validated_05(self):
        self.assertEqual(self.event.state, 'draft')
        self.event.button_confirm()
        self.assertEqual(self.event.state, 'confirm')
        self.assertEqual(self.registration.state, 'draft')
        self.registration.confirm_registration()
        self.assertEqual(self.registration.state, 'open')
        self.registration.button_reg_close()
        self.assertEqual(self.registration.state, 'done')
        wizard = self.env['event.registration.barcodes'].create({
            'event_id': self.event.id,
        })
        wizard._origin = wizard
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        wizard.read_event_ticket(self.registration.barcode)
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        self.assertEqual(wizard.message_type, 'done')
        self.assertEqual(
            wizard.message, _('Ticket has already been validated'))

    def test_try_repeat_validation_ticket_in_same_wizard(self):
        self.assertEqual(self.event.state, 'draft')
        self.event.button_confirm()
        self.assertEqual(self.event.state, 'confirm')
        self.assertEqual(self.registration.state, 'draft')
        self.registration.confirm_registration()
        self.assertEqual(self.registration.state, 'open')
        wizard = self.env['event.registration.barcodes'].create({
            'event_id': self.event.id,
        })
        wizard._origin = wizard
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        wizard.read_event_ticket(self.registration.barcode)
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 1)
        self.assertEqual(wizard.message_type, 'success')
        self.assertEqual(wizard.message, 'Ticket successfully validated')
        self.assertEqual(self.registration.state, 'done')
        wizard.read_event_ticket(self.registration.barcode)
        self.assertEqual(
            wizard.message, _('Ticket has already been validated'))
        self.assertEqual(wizard.message_type, 'done')

    def test_registration_cancel_06(self):
        self.assertEqual(self.event.state, 'draft')
        self.event.button_confirm()
        self.assertEqual(self.event.state, 'confirm')
        self.assertEqual(self.registration.state, 'draft')
        self.registration.button_reg_cancel()
        self.assertEqual(self.registration.state, 'cancel')
        wizard = self.env['event.registration.barcodes'].create({
            'event_id': self.event.id,
        })
        wizard._origin = wizard
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        wizard.read_event_ticket(self.registration.barcode)
        wizard.with_context(wizard_id=wizard.id)._compute_line_ids()
        self.assertEqual(
            len(wizard.with_context(wizard_id=wizard.id).line_ids), 0)
        self.assertEqual(wizard.message_type, 'cancel')
        self.assertEqual(wizard.message, _('Ticket is canceled'))

    def test_constraint_barcode_registration_unique_same_event_07(self):
        registration_02 = self.env['event.registration'].create({
            'event_id': self.event.id,
            'partner_id': self.partner.id,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            registration_02.barcode = self.registration.barcode
        self.assertEqual(
            result.exception.name,
            _('The barcode %s already exists in another ticket') % (
                self.registration.barcode))

    def test_constraint_barcode_registration_unique_not_same_event_08(self):
        event_02 = self.env['event.event'].create({
            'name': 'Test event 2',
            'date_begin': datetime.now(),
            'date_end': datetime.now() + relativedelta(days=7),
        })
        registration_02 = self.env['event.registration'].create({
            'event_id': event_02.id,
            'partner_id': self.partner.id,
        })
        self.assertNotEqual(
            self.registration.event_id, registration_02.event_id)
        self.assertNotEqual(self.registration.barcode, registration_02.barcode)
        with self.assertRaises(exceptions.ValidationError) as result:
            registration_02.barcode = self.registration.barcode
        self.assertEqual(
            result.exception.name,
            _('The barcode %s already exists in another ticket') % (
                self.registration.barcode))
