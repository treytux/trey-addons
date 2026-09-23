###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import odoo.tests
from odoo import Command, fields, http
from odoo.addons.portal_academy.controllers.portal import CustomerPortal


@odoo.tests.tagged('post_install', '-at_install')
class TestPortalAcademy(odoo.tests.HttpCase):

    def setUp(self):
        super().setUp()
        self.portal_password = 'portal_academy_test'
        self.user_admin = self.env.ref('base.user_admin')
        self.group_portal = self.env.ref('base.group_portal')
        self.group_academy_tutor = self.env.ref('academy.group_academy_tutor')
        self.group_academy_student = self.env.ref(
            'academy.group_academy_student')
        self.tutor_a_partner = self.env['res.partner'].create({
            'name': 'Tutor A',
            'is_tutor': True,
            'email': 'tutor_a@test.com',
        })
        self.tutor_b_partner = self.env['res.partner'].create({
            'name': 'Tutor B',
            'is_tutor': True,
            'email': 'tutor_b@test.com',
        })
        self.tutor_a_partner.write({
            'vat': 'ES12345678Z',
        })
        self.student_a_partner = self.env['res.partner'].create({
            'name': 'Student A',
            'is_student': True,
            'tutor_ids': [Command.set(self.tutor_a_partner.ids)],
            'email': 'student_a@test.com',
        })
        self.student_b_partner = self.env['res.partner'].create({
            'name': 'Student B',
            'is_student': True,
            'tutor_ids': [Command.set(self.tutor_b_partner.ids)],
            'email': 'student_b@test.com',
        })
        self.tutor_a_login = 'tutor_a_portal'
        self.tutor_b_login = 'tutor_b_portal'
        self.student_a_login = 'student_a_portal'
        self.tutor_a_user = self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': 'Tutor A Portal',
                'login': self.tutor_a_login,
                'email': 'tutor_a_portal@test.com',
                'password': self.portal_password,
                'partner_id': self.tutor_a_partner.id,
                'groups_id': [Command.set([
                    self.group_portal.id,
                    self.group_academy_tutor.id,
                ])],
            })
        self.tutor_b_user = self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': 'Tutor B Portal',
                'login': self.tutor_b_login,
                'email': 'tutor_b_portal@test.com',
                'password': self.portal_password,
                'partner_id': self.tutor_b_partner.id,
                'groups_id': [Command.set([
                    self.group_portal.id,
                    self.group_academy_tutor.id,
                ])],
            })
        self.student_a_user = self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': 'Student A Portal',
                'login': self.student_a_login,
                'email': 'student_a_portal@test.com',
                'password': self.portal_password,
                'partner_id': self.student_a_partner.id,
                'groups_id': [Command.set([
                    self.group_portal.id,
                    self.group_academy_student.id,
                ])],
            })
        self.teacher = self.env['hr.employee'].create({
            'name': 'Portal Teacher',
        })
        tutor_bank = self.env['res.partner.bank'].create({
            'partner_id': self.tutor_a_partner.id,
            'acc_number': 'ES9121000418450200051332',
        })
        self.tutor_mandate = self.env['account.banking.mandate'].create({
            'partner_bank_id': tutor_bank.id,
            'signature_date': fields.Date.today(),
        })
        self.tutor_mandate.validate()
        self.academic_training = self.env['academy.academic.training'].create({
            'name': 'Portal Academic Training',
        })
        self.evaluation_a = self.env['academy.evaluation'].create({
            'name': 'Evaluation A',
            'sequence': 1,
        })
        self.evaluation_b = self.env['academy.evaluation'].create({
            'name': 'Evaluation B',
            'sequence': 2,
        })
        self.concept = self.env['academy.evaluable.concept'].create({
            'name': 'Portal Concept',
        })
        self.mark_a = self.env['academy.evaluable.concept.mark'].create({
            'name': 'Mark A',
        })
        self.mark_b = self.env['academy.evaluable.concept.mark'].create({
            'name': 'Mark B',
        })
        today = fields.Date.today()
        start_date = today - timedelta(days=15)
        end_date = today + timedelta(days=30)
        self.training_plan_visible = self.env['academy.training.plan'].create({
            'name': 'Visible Plan',
            'start_date': start_date,
            'end_date': end_date,
            'user_id': self.user_admin.id,
            'visible_website': True,
        })
        self.training_plan_hidden = self.env['academy.training.plan'].create({
            'name': 'Hidden Plan',
            'start_date': start_date,
            'end_date': end_date,
            'user_id': self.user_admin.id,
            'visible_website': False,
        })
        self.activity_student_a = self.env['academy.activity'].create({
            'name': 'Visible Activity Student A',
            'training_plan_id': self.training_plan_visible.id,
            'user_id': self.user_admin.id,
            'teacher_id': self.teacher.id,
            'start_date': start_date,
            'end_date': end_date,
            'state': 'active',
            'visible_website': True,
        })
        self.activity_student_b = self.env['academy.activity'].create({
            'name': 'Visible Activity Student B',
            'training_plan_id': self.training_plan_visible.id,
            'user_id': self.user_admin.id,
            'teacher_id': self.teacher.id,
            'start_date': start_date,
            'end_date': end_date,
            'state': 'active',
            'visible_website': True,
        })
        self.activity_new_enrollment = self.env['academy.activity'].create({
            'name': 'Visible Activity New Enrollment',
            'training_plan_id': self.training_plan_visible.id,
            'user_id': self.user_admin.id,
            'teacher_id': self.teacher.id,
            'start_date': start_date,
            'end_date': end_date,
            'state': 'active',
            'visible_website': True,
        })
        self.activity_hidden = self.env['academy.activity'].create({
            'name': 'Hidden Activity',
            'training_plan_id': self.training_plan_hidden.id,
            'user_id': self.user_admin.id,
            'teacher_id': self.teacher.id,
            'start_date': start_date,
            'end_date': end_date,
            'state': 'active',
            'visible_website': False,
        })
        self.enrollment_student_a = self.env['academy.enrollment'].create({
            'training_plan_id': self.training_plan_visible.id,
            'activity_id': self.activity_student_a.id,
            'student_id': self.student_a_partner.id,
            'tutor_ids': [Command.set(self.tutor_a_partner.ids)],
            'start_date': today,
            'end_date': today,
            'state': 'active',
        })
        self.enrollment_student_b = self.env['academy.enrollment'].create({
            'training_plan_id': self.training_plan_visible.id,
            'activity_id': self.activity_student_b.id,
            'student_id': self.student_b_partner.id,
            'tutor_ids': [Command.set(self.tutor_b_partner.ids)],
            'start_date': today,
            'end_date': today,
            'state': 'active',
        })
        self.bulletin_student_a = self.env['academy.marks.bulletin'].create({
            'name': self.student_a_partner.id,
            'enrollment_id': self.enrollment_student_a.id,
        })
        self.bulletin_student_b = self.env['academy.marks.bulletin'].create({
            'name': self.student_b_partner.id,
            'enrollment_id': self.enrollment_student_b.id,
        })
        self.env['academy.marks.bulletin.line'].create({
            'bulletin_id': self.bulletin_student_a.id,
            'student_id': self.student_a_partner.id,
            'evaluation_id': self.evaluation_a.id,
            'evaluable_concept_id': self.concept.id,
            'eval_concept_mark_id': self.mark_a.id,
            'portal_published': True,
        })
        self.env['academy.marks.bulletin.line'].create({
            'bulletin_id': self.bulletin_student_b.id,
            'student_id': self.student_b_partner.id,
            'evaluation_id': self.evaluation_b.id,
            'evaluable_concept_id': self.concept.id,
            'eval_concept_mark_id': self.mark_b.id,
            'portal_published': True,
        })
        sheet_a = self.env['academy.attendance.sheet'].create({
            'date': today,
            'teacher_id': self.teacher.id,
            'activity_id': self.activity_student_a.id,
            'state': 'ready',
            'filters': 'all',
        })
        sheet_b = self.env['academy.attendance.sheet'].create({
            'date': today,
            'teacher_id': self.teacher.id,
            'activity_id': self.activity_student_b.id,
            'state': 'ready',
            'filters': 'all',
        })
        self.env['academy.attendance.sheet.line'].create({
            'attendance_sheet_id': sheet_a.id,
            'student_id': self.student_a_partner.id,
            'present': False,
            'comments': 'ABSENCE-STUDENT-A',
        })
        self.env['academy.attendance.sheet.line'].create({
            'attendance_sheet_id': sheet_b.id,
            'student_id': self.student_b_partner.id,
            'present': False,
            'comments': 'ABSENCE-STUDENT-B',
        })

    def _authenticate_as(self, login):
        self.authenticate(login, self.portal_password)
        http.root.session_store.save(self.session)

    def _new_enrollment_post_data(
            self, student_id, accept_terms=True, start_date=None):
        data = {
            'csrf_token': http.Request.csrf_token(self),
            'student_id': str(student_id),
            'birthdate_date': '2015-01-01',
            'academic_training_id': str(self.academic_training.id),
            'training_plan_id': str(self.training_plan_visible.id),
            'activity_id': str(self.activity_new_enrollment.id),
            'start_date': start_date or fields.Date.to_string(
                fields.Date.today()),
        }
        if accept_terms:
            data['accept_terms'] = 'on'
        return data

    def _new_student_post_data(self):
        return {
            'csrf_token': http.Request.csrf_token(self),
            'name': 'Student Created From Portal',
            'birthdate_date': '2015-01-01',
            'academic_training_id': str(self.academic_training.id),
        }

    def test_tutor_not_authorized_cannot_see_other_student_data(self):
        self._authenticate_as(self.tutor_a_login)
        response_absences = self.url_open(
            '/my/absences-training-lines/%s/' % self.student_b_partner.id)
        self.assertEqual(response_absences.status_code, 200)
        self.assertIn('/my', response_absences.url)
        response_bulletins = self.url_open(
            '/my/bulletins/%s' % self.student_b_partner.id)
        self.assertEqual(response_bulletins.status_code, 200)
        self.assertIn('/my', response_bulletins.url)
        response_evaluations = self.url_open(
            '/my/evaluations/%s' % self.bulletin_student_b.id)
        self.assertEqual(response_evaluations.status_code, 200)
        self.assertIn('/my', response_evaluations.url)

    def test_student_only_sees_own_absences_bulletins_and_evaluations(self):
        self._authenticate_as(self.student_a_login)
        response_absences = self.url_open(
            '/my/absences/%s' % self.activity_student_a.id)
        self.assertEqual(response_absences.status_code, 200)
        self.assertIn('ABSENCE-STUDENT-A', response_absences.text)
        self.assertNotIn('ABSENCE-STUDENT-B', response_absences.text)
        response_bulletins = self.url_open('/my/bulletins')
        self.assertEqual(response_bulletins.status_code, 200)
        self.assertIn(self.activity_student_a.name, response_bulletins.text)
        self.assertNotIn(self.activity_student_b.name, response_bulletins.text)
        response_evaluations = self.url_open(
            '/my/evaluations/%s' % self.bulletin_student_a.id)
        self.assertEqual(response_evaluations.status_code, 200)
        self.assertIn(self.evaluation_a.name, response_evaluations.text)
        self.assertIn(self.mark_a.name, response_evaluations.text)
        self.assertNotIn(self.evaluation_b.name, response_evaluations.text)
        self.assertNotIn(self.mark_b.name, response_evaluations.text)

    def test_prepare_home_portal_values_returns_correct_counters(self):
        controller = CustomerPortal()
        with patch(
            'odoo.addons.portal_academy.controllers.portal.request',
            SimpleNamespace(env=self.env(user=self.student_a_user.id))
        ):
            student_values = controller._prepare_home_portal_values([
                'absence_count', 'bulletin_count'])
        self.assertEqual(student_values['absence_count'], 1)
        self.assertEqual(student_values['bulletin_count'], 1)
        with patch(
            'odoo.addons.portal_academy.controllers.portal.request',
            SimpleNamespace(env=self.env(user=self.tutor_a_user.id))
        ):
            tutor_values = controller._prepare_home_portal_values([
                'students_count', 'enrollment_count'])
        self.assertEqual(tutor_values['students_count'], 1)
        self.assertEqual(tutor_values['enrollment_count'], 1)

    def test_tutor_can_see_own_student_enrollments(self):
        self._authenticate_as(self.tutor_a_login)
        response = self.url_open('/my/enrollments')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.enrollment_student_a.name, response.text)
        self.assertIn(self.student_a_partner.name, response.text)
        self.assertNotIn(self.enrollment_student_b.name, response.text)
        self.assertNotIn(self.student_b_partner.name, response.text)

    def test_student_cannot_see_tutor_enrollments(self):
        self._authenticate_as(self.student_a_login)
        response = self.url_open('/my/enrollments')
        self.assertEqual(response.status_code, 200)
        self.assertIn('/my', response.url)

    def test_new_enrollment_submit_fails_without_accept_terms(self):
        self._authenticate_as(self.tutor_a_login)
        enrollments_before = self.env['academy.enrollment'].search_count([
            ('student_id', '=', self.student_a_partner.id),
            ('activity_id', '=', self.activity_new_enrollment.id),
        ])
        response = self.url_open(
            '/my/new-enrollment/submit',
            data=self._new_enrollment_post_data(
                self.student_a_partner.id, accept_terms=False))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'You must accept the terms and privacy policy.',
            response.text)
        enrollments_after = self.env['academy.enrollment'].search_count([
            ('student_id', '=', self.student_a_partner.id),
            ('activity_id', '=', self.activity_new_enrollment.id),
        ])
        self.assertEqual(enrollments_before, enrollments_after)

    def test_new_enrollment_submit_requires_customer_data(self):
        enrollments_before = self.env['academy.enrollment'].search_count([
            ('student_id', '=', self.student_b_partner.id),
            ('activity_id', '=', self.activity_new_enrollment.id),
        ])
        self._authenticate_as(self.tutor_b_login)
        response = self.url_open(
            '/my/new-enrollment/submit',
            data=self._new_enrollment_post_data(self.student_b_partner.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Please complete your customer name and VAT number before '
            'enrolling.', response.text)
        enrollments_after = self.env['academy.enrollment'].search_count([
            ('student_id', '=', self.student_b_partner.id),
            ('activity_id', '=', self.activity_new_enrollment.id),
        ])
        self.assertEqual(enrollments_before, enrollments_after)

    def test_enrollment_requires_valid_mandate(self):
        partner = self.env['res.partner'].create({
            'name': 'Tutor Without Mandate',
            'vat': 'ES12345678Z',
            'is_tutor': True,
        })
        self.env['res.partner.bank'].create({
            'partner_id': partner.id,
            'acc_number': 'ES6421000418450200051333',
        })
        self.env['account.banking.mandate'].search([
            ('partner_bank_id', 'in', partner.bank_ids.ids),
        ]).write({'state': 'cancel'})
        self.assertEqual(
            partner._portal_enrollment_requirement_error(),
            'A valid SEPA mandate is required before enrolling.')

    def test_new_enrollment_submit_fails_with_invalid_student(self):
        self._authenticate_as(self.tutor_a_login)
        enrollments_before = self.env['academy.enrollment'].search_count([
            ('student_id', '=', self.student_b_partner.id),
            ('activity_id', '=', self.activity_new_enrollment.id),
        ])
        response = self.url_open(
            '/my/new-enrollment/submit', data=self._new_enrollment_post_data(
                self.student_b_partner.id, accept_terms=True))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Invalid student selected.', response.text)
        enrollments_after = self.env['academy.enrollment'].search_count([
            ('student_id', '=', self.student_b_partner.id),
            ('activity_id', '=', self.activity_new_enrollment.id),
        ])
        self.assertEqual(enrollments_before, enrollments_after)

    def test_new_enrollment_submit_fails_with_past_start_date(self):
        self._authenticate_as(self.tutor_a_login)
        enrollments_before = self.env['academy.enrollment'].search_count([
            ('student_id', '=', self.student_a_partner.id),
            ('activity_id', '=', self.activity_new_enrollment.id),
        ])
        past_date = fields.Date.to_string(
            fields.Date.today() - timedelta(days=1))
        response = self.url_open(
            '/my/new-enrollment/submit',
            data=self._new_enrollment_post_data(
                self.student_a_partner.id, accept_terms=True,
                start_date=past_date))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Start date cannot be in the past.', response.text)
        enrollments_after = self.env['academy.enrollment'].search_count([
            ('student_id', '=', self.student_a_partner.id),
            ('activity_id', '=', self.activity_new_enrollment.id),
        ])
        self.assertEqual(enrollments_before, enrollments_after)

    def test_new_enrollment_submit_creates_enrollment_on_valid_case(self):
        self._authenticate_as(self.tutor_a_login)
        enrollments_before = self.env['academy.enrollment'].search_count([
            ('student_id', '=', self.student_a_partner.id),
            ('activity_id', '=', self.activity_new_enrollment.id),
        ])
        response = self.url_open(
            '/my/new-enrollment/submit',
            data=self._new_enrollment_post_data(
                self.student_a_partner.id, accept_terms=True))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            '/my/activities/%s' % self.student_a_partner.id, response.url)
        enrollments_after = self.env['academy.enrollment'].search_count([
            ('student_id', '=', self.student_a_partner.id),
            ('activity_id', '=', self.activity_new_enrollment.id),
        ])
        self.assertEqual(enrollments_after, enrollments_before + 1)

    def test_new_enrollment_page_shows_only_visible_website_records(self):
        self._authenticate_as(self.tutor_a_login)
        response = self.url_open('/my/new-enrollment')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.training_plan_visible.name, response.text)
        self.assertIn(self.activity_new_enrollment.name, response.text)
        self.assertNotIn(self.training_plan_hidden.name, response.text)
        self.assertNotIn(self.activity_hidden.name, response.text)

    def test_tutor_can_open_new_student_form(self):
        self._authenticate_as(self.tutor_a_login)
        response = self.url_open('/my/students')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Create student', response.text)
        response = self.url_open('/my/student/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Surname and first name', response.text)
        self.assertIn('Date of birth', response.text)
        self.assertIn('Course', response.text)

    def test_tutor_can_find_customer_details_edit_link(self):
        self._authenticate_as(self.tutor_a_login)
        response = self.url_open('/my/home')
        self.assertEqual(response.status_code, 200)
        self.assertIn('href="/my/account"', response.text)
        self.assertIn('Edit customer details', response.text)

    def test_tutor_can_create_student_from_portal(self):
        self._authenticate_as(self.tutor_a_login)
        response = self.url_open(
            '/my/student/new/save', data=self._new_student_post_data())
        self.assertEqual(response.status_code, 200)
        self.assertIn('/my/student/', response.url)
        student = self.env['res.partner'].search([
            ('name', '=', 'Student Created From Portal'),
        ], limit=1)
        self.assertTrue(student)
        self.assertTrue(student.is_student)
        self.assertIn(self.tutor_a_partner, student.tutor_ids)
        self.assertEqual(
            fields.Date.to_string(student.birthdate_date), '2015-01-01')
        self.assertEqual(student.academic_training_ids, self.academic_training)

    def test_non_tutor_cannot_create_student_from_portal(self):
        self._authenticate_as(self.student_a_login)
        response = self.url_open('/my/student/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn('/my', response.url)

    def test_bank_form_requires_sepa_acceptance(self):
        self._authenticate_as(self.tutor_a_login)
        response = self.url_open('/my/bank/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="accept_sepa"', response.text)
        self.assertNotIn('name="bank_id"', response.text)
        banks_before = self.env['res.partner.bank'].search_count([
            ('partner_id', '=', self.tutor_a_partner.id),
        ])
        response = self.url_open('/my/bank/new/submit', data={
            'csrf_token': http.Request.csrf_token(self),
            'acc_number': 'ES6421000418450200051333',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('You must accept the SEPA conditions.', response.text)
        banks_after = self.env['res.partner.bank'].search_count([
            ('partner_id', '=', self.tutor_a_partner.id),
        ])
        self.assertEqual(banks_before, banks_after)
        response = self.url_open('/my/bank/new/submit', data={
            'csrf_token': http.Request.csrf_token(self),
            'acc_number': 'ES6421000418450200051333',
            'accept_sepa': 'on',
        })
        bank = self.env['res.partner.bank'].search([
            ('partner_id', '=', self.tutor_a_partner.id),
            ('acc_number', '=', 'ES64 2100 0418 4502 0005 1333'),
        ], limit=1)
        self.assertTrue(bank)
        self.assertTrue(bank.bank_id)
