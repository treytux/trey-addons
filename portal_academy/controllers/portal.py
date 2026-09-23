###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
from datetime import date, timedelta

from odoo import _, fields
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import UserError, ValidationError
from odoo.http import request, route


class CustomerPortal(CustomerPortal):
    OPTIONAL_BILLING_FIELDS = CustomerPortal.OPTIONAL_BILLING_FIELDS + [
        'mobile',
        'zip_id',
    ]

    def details_form_validate(self, data, partner_creation=False):
        error, error_message = super().details_form_validate(
            data, partner_creation=partner_creation)
        partner = request.env.user.partner_id
        if partner.is_tutor and not data.get('vat'):
            error['vat'] = 'missing'
            error_message.append(_('VAT number is required.'))
        return error, error_message

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        absence_count = 0
        bulletin_count = 0
        students_count = 0
        enrollment_count = 0
        if partner.is_student:
            attendance = request.env['academy.attendance.sheet.line']
            bulletin = request.env['academy.marks.bulletin']
            absence_count = attendance.search_count([
                ('student_id', '=', partner.id),
                ('attendance_sheet_id.state', 'not in', [
                    'draft', 'cancelled']),
                ('present', '=', False),
            ])
            bulletin_count = bulletin.search_count([
                ('name', '=', partner.id),
                ('bulletin_line_ids', '!=', False),
                ('bulletin_line_ids.portal_published', '=', True),
            ])
        elif partner.is_tutor:
            students_count = len(partner.student_ids)
            enrollment_count = request.env[
                'academy.enrollment'].sudo().search_count([
                    ('student_id.tutor_ids', 'in', partner.id),
                ])
        if 'students_count' in counters:
            values['students_count'] = students_count
        if 'absence_count' in counters:
            values['absence_count'] = absence_count
        if 'bulletin_count' in counters:
            values['bulletin_count'] = bulletin_count
        if 'enrollment_count' in counters:
            values['enrollment_count'] = enrollment_count
        return values

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        if partner.is_student:
            attendance = request.env['academy.attendance.sheet.line']
            bulletin = request.env['academy.marks.bulletin']
            absence_count = attendance.search_count([
                ('student_id', '=', partner.id),
                ('attendance_sheet_id.state', 'not in', [
                    'draft', 'cancelled']),
                ('present', '=', False),
            ])
            bulletin_count = bulletin.search_count([
                ('name', '=', partner.id),
                ('bulletin_line_ids', '!=', False),
            ])
            values.update({
                'absence_count': absence_count,
                'bulletin_count': bulletin_count,
            })
        elif partner.is_tutor:
            values.update({
                'students_count': len(partner.student_ids),
            })
        return values

    def _prepare_enrollment_vals(
            self, form_values, student, activity, start_date, reduced_price):
        current_user = request.env.user
        return {
            'student_id': student.id,
            'training_plan_id': form_values['training_plan_id'],
            'activity_id': activity.id,
            'start_date': start_date,
            'end_date': activity.end_date,
            'reduced_price': reduced_price,
            'tutor_ids': [current_user.partner_id.id],
            'academic_training_ids': [
                (6, 0, student.academic_training_ids.ids),
            ],
        }

    @route(['/my/students'], type='http', auth='user', website=True)
    def portal_my_students(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        if not partner.is_tutor:
            return request.redirect('/my')
        student = request.env['res.partner']
        domain = [
            ('id', 'in', partner.student_ids.ids),
        ]
        searchbar_sortings = {
            'name': {
                'label': _('Name'),
                'order': 'name',
            },
        }
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']
        pager = portal_pager(
            url='/my/students',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
            },
            total=len(partner.student_ids),
            page=page,
            step=self._items_per_page)
        students = student.sudo().search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_students_history'] = students.ids[:100]
        values.update({
            'date': date_begin,
            'students': students,
            'page_name': 'students',
            'pager': pager,
            'default_url': '/my/students',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render('portal_academy.portal_my_students', values)

    @route(['/my/enrollments'], type='http', auth='user', website=True)
    def portal_my_enrollments(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        if not partner.is_tutor:
            return request.redirect('/my')
        enrollment = request.env['academy.enrollment'].sudo()
        domain = [
            ('student_id.tutor_ids', 'in', partner.id),
        ]
        searchbar_sortings = {
            'start_date': {
                'label': _('Start Date'),
                'order': 'start_date asc, id asc',
            },
            'student': {
                'label': _('Student'),
                'order': 'student_id, start_date asc, id asc',
            },
        }
        if not sortby:
            sortby = 'start_date'
        sort_order = searchbar_sortings[sortby]['order']
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        enrollment_count = enrollment.search_count(domain)
        pager = portal_pager(
            url='/my/enrollments',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
            },
            total=enrollment_count, page=page, step=self._items_per_page)
        enrollments = enrollment.search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_enrollments_history'] = enrollments.ids[:100]
        values.update({
            'date': date_begin,
            'enrollments': enrollments,
            'page_name': 'enrollments',
            'pager': pager,
            'default_url': '/my/enrollments',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'today': date.today(),
        })
        return request.render('portal_academy.portal_my_enrollments', values)

    def _portal_student_form_values(self, post=None):
        post = post or {}
        return {
            'name': post.get('name', ''),
            'birthdate_date': post.get('birthdate_date', ''),
            'academic_training_id': post.get('academic_training_id', ''),
        }

    def _portal_student_form_data(self, error=None, form_values=None):
        return {
            'page_name': 'student_new',
            'error': error,
            'form_values': form_values or self._portal_student_form_values(),
            'academic_trainings': (
                request.env['academy.academic.training'].sudo().search([
                    ('type', '!=', 'teacher'),
                ], order='name asc')),
        }

    def _portal_student_form_training(self, form_values):
        try:
            training_id = int(form_values['academic_training_id'] or 0)
        except (TypeError, ValueError):
            training_id = 0
        training = request.env['academy.academic.training'].sudo().search([
            ('id', '=', training_id),
            ('type', '!=', 'teacher'),
        ], limit=1)
        return training

    @route(['/my/student/new'], type='http', auth='user', website=True)
    def portal_student_new(self, error=None, form_values=None, **kw):
        if not request.env.user.partner_id.is_tutor:
            return request.redirect('/my')
        return request.render(
            'portal_academy.portal_student_new',
            self._portal_student_form_data(error, form_values))

    @route(['/my/student/new/save'], type='http', auth='user', website=True)
    def portal_student_new_save(self, **post):
        tutor = request.env.user.partner_id
        if not tutor.is_tutor:
            return request.redirect('/my')
        form_values = self._portal_student_form_values(post)
        if not form_values['name'].strip():
            return self.portal_student_new(
                error='The student name is required.',
                form_values=form_values)
        training = self._portal_student_form_training(form_values)
        if not training:
            return self.portal_student_new(
                error='The selected course is invalid.',
                form_values=form_values)
        try:
            with request.env.cr.savepoint():
                student = request.env['res.partner'].sudo().create({
                    'name': form_values['name'].strip(),
                    'birthdate_date': form_values['birthdate_date'],
                    'is_student': True,
                    'academic_training_ids': [(6, 0, training.ids)],
                    'tutor_ids': [(4, tutor.id)],
                })
        except (ValidationError, UserError) as e:
            return self.portal_student_new(
                error=str(e), form_values=form_values)
        except Exception:
            return self.portal_student_new(
                error='Unexpected error while creating the student.',
                form_values=form_values)
        return request.redirect('/my/student/%s' % student.id)

    @route(
        ['/my/absences-training-lines/',
         '/my/absences-training-lines/<int:student_id>/'],
        type='http', auth='user', website=True)
    def portal_my_absences_training_lines(
            self, student_id=None, activity_id=None, page=1,
            date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        if student_id and student_id not in partner.student_ids.ids:
            return request.redirect('/my')
        if not student_id and partner.is_student:
            student_id = partner.id
            values.update({
                'is_student': True,
            })
        student = request.env['res.partner'].browse(student_id)
        attendances = request.env['academy.attendance.sheet.line'].search([
            ('student_id', '=', student_id),
            ('attendance_sheet_id.state', 'not in', ['draft', 'cancelled']),
            ('present', '=', False),
        ])
        activity_lines = attendances.mapped('activity_id')
        domain = [
            ('id', 'in', activity_lines.ids),
            ('state', '=', 'active'),
        ]
        searchbar_sortings = {
            'name': {
                'label': _('Title'),
                'order': 'name',
            },
        }
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        trainings_count = len(activity_lines)
        pager = portal_pager(
            url='/my/absences-training-lines',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
            },
            total=trainings_count, page=page, step=self._items_per_page)
        activity_lines = activity_lines.search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_absences_history'] = activity_lines.ids[:100]
        values.update({
            'date': date_begin,
            'student': student,
            'activity_lines': activity_lines,
            'page_name': 'absences',
            'pager': pager,
            'default_url': '/my/absences-training-lines',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render(
            'portal_academy.portal_my_absences_training_line', values)

    @route(
        ['/my/absences/<int:student_id>/<int:line_id>',
         '/my/absences/<int:line_id>'], type='http', auth='user', website=True)
    def portal_my_absences(
            self, student_id=None, line_id=None, page=1, date_begin=None,
            date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        if student_id and student_id not in partner.student_ids.ids:
            return request.redirect('/my')
        if not student_id and partner.is_student:
            student_id = partner.id
            values.update({'is_student': True})
        student = request.env['res.partner'].browse(student_id)
        attendance = request.env['academy.attendance.sheet.line']
        domain = [
            ('student_id', '=', student_id),
            ('attendance_sheet_id.state', 'not in', ['draft', 'cancelled']),
            ('present', '=', False),
            ('activity_id', '=', line_id),
        ]
        searchbar_sortings = {
            'name': {
                'label': _('Title'),
                'order': 'date',
            },
        }
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        absence_count = attendance.search_count(domain)
        pager = portal_pager(
            url='/my/absences',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
            },
            total=absence_count, page=page, step=self._items_per_page)
        absences = attendance.search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_absences_history'] = absences.ids[:100]
        values.update({
            'date': date_begin,
            'student': student,
            'absences': absences,
            'page_name': 'absences',
            'pager': pager,
            'default_url': '/my/absences',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render('portal_academy.portal_my_absences', values)

    @route(
        ['/my/bulletins', '/my/bulletins/<int:student_id>'], type='http',
        auth='user', website=True)
    def portal_my_bulletins(
            self, student_id=None, page=1, date_begin=None, date_end=None,
            sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        if student_id and student_id not in partner.student_ids.ids:
            return request.redirect('/my')
        if not student_id and partner.is_student:
            student_id = partner.id
            values.update({'is_student': True})
        student = request.env['res.partner'].browse(student_id)
        bulletin = request.env['academy.marks.bulletin']
        domain = [
            ('name', '=', student_id),
            ('bulletin_line_ids', '!=', False),
            ('bulletin_line_ids.portal_published', '=', True),
        ]
        searchbar_sortings = {
            'name': {
                'label': _('Title'),
                'order': 'year',
            },
        }
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        bulletin_count = bulletin.search_count(domain)
        pager = portal_pager(
            url='/my/bulletins',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
            },
            total=bulletin_count, page=page, step=self._items_per_page)
        bulletins = bulletin.search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_bulletins_history'] = bulletins.ids[:100]
        values.update({
            'date': date_begin,
            'student': student,
            'bulletins': bulletins,
            'page_name': 'bulletins',
            'pager': pager,
            'default_url': '/my/bulletins',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render('portal_academy.portal_my_bulletins', values)

    @route(
        ['/my/evaluations/<int:bulletin_id>'], type='http', auth='user',
        website=True, csrf=False)
    def portal_my_evaluation(self, bulletin_id, **kw):
        partner = request.env.user.partner_id
        evaluations = request.env['academy.marks.bulletin.line'].search([
            ('bulletin_id', '=', bulletin_id),
            ('portal_published', '=', True),
        ])
        if not evaluations:
            return request.redirect('/my')
        student = evaluations.mapped('student_id')
        if partner.is_student and student != partner:
            return request.redirect('/my')
        if partner.is_tutor and student not in partner.student_ids:
            return request.redirect('/my')
        values = {
            'is_student': request.env.user.partner_id.is_student,
            'student': student,
            'bulletin': evaluations.mapped('bulletin_id'),
            'evaluations': evaluations,
            'page_name': 'bulletins',
        }
        return request.render('portal_academy.portal_my_evaluations', values)

    @route(['/my/new-enrollment'], type='http', auth='user', website=True)
    def portal_new_enrollment(self, error=None, form_values=None, **post):
        partner = request.env.user.partner_id
        training_plans = request.env['academy.training.plan'].search([
            ('active', '=', True),
            ('visible_website', '=', True),
        ], order='name asc')
        activities = request.env['academy.activity'].search([
            ('visible_website', '=', True),
        ], order='name asc')
        academic_trainings = request.env['academy.academic.training'].search([
            ('type', 'in', ['student', 'both']),
        ], order='name asc')
        students_payload = []
        for s in partner.student_ids:
            students_payload.append({
                'id': s.id,
                'name': s.name or '',
                'birthdate': (
                    s.birthdate_date.isoformat() if s.birthdate_date else ''),
                'academic_training_ids': s.academic_training_ids.ids or [],
            })
        values = {
            'page_name': 'new_enrollment',
            'students': partner.student_ids,
            'students_json': json.dumps(students_payload),
            'training_plans': training_plans,
            'academic_trainings': academic_trainings,
            'activities': activities,
            'selected_student': None,
            'today': date.today().isoformat(),
            'error': error,
            'form_values': form_values or {},
        }
        return request.render('portal_academy.portal_new_enrollment', values)

    @route(
        ['/my/new-enrollment/submit'], type='http', auth='user', website=True)
    def portal_new_enrollment_submit(self, **post):
        current_user = request.env.user
        requirement_error = (
            current_user.partner_id._portal_enrollment_requirement_error())
        if requirement_error:
            return self.portal_new_enrollment(error=requirement_error)
        form_values = {
            'student_id': int(post.get('student_id') or 0),
            'birthdate_date': post.get('birthdate_date'),
            'academic_training_id': int(post.get('academic_training_id')),
            'has_allergy': post.get('has_allergy') == 'on',
            'allergy_description': post.get('allergy_description') or '',
            'apa_member': post.get('apa_member') == 'on',
            'apa_member_number': post.get('apa_member_number') or '',
            'training_plan_id': int(post.get('training_plan_id') or 0),
            'activity_id': int(post.get('activity_id') or 0),
            'start_date': post.get('start_date'),
        }
        if not post.get('accept_terms') == 'on':
            return self.portal_new_enrollment(
                error='You must accept the terms and privacy policy.',
                form_values=form_values)
        student = request.env['res.partner'].sudo().search([
            ('id', '=', form_values['student_id']),
            ('tutor_ids', 'in', current_user.partner_id.id),
            ('is_student', '=', True),
        ])
        if not student:
            return self.portal_new_enrollment(
                error='Invalid student selected.', form_values=form_values)
        activity = request.env['academy.activity'].sudo().browse(
            form_values['activity_id'])
        if not activity.exists():
            return self.portal_new_enrollment(
                error='Invalid activity selected.', form_values=form_values)
        if (
            form_values['has_allergy']
                and not form_values['allergy_description']):
            return self.portal_new_enrollment(
                error='Allergy description is required when allergies are '
                'indicated.', form_values=form_values)
        try:
            with request.env.cr.savepoint():
                start_date = fields.Date.from_string(form_values['start_date'])
        except Exception:
            return self.portal_new_enrollment(
                error='Invalid start date format.', form_values=form_values)
        if start_date < date.today():
            return self.portal_new_enrollment(
                error='Start date cannot be in the past.',
                form_values=form_values)
        if activity.start_date and start_date < activity.start_date:
            return self.portal_new_enrollment(
                error='Start date must be within the activity date range.',
                form_values=form_values)
        if activity.end_date and start_date > activity.end_date:
            return self.portal_new_enrollment(
                error='Start date must be within the activity date range.',
                form_values=form_values)
        reduced_price = False
        if form_values['apa_member']:
            reduced_price = True
            if not form_values['apa_member_number']:
                return self.portal_new_enrollment(
                    error='Membership number is required for APA/AMPA '
                    'members.', form_values=form_values)
        enrollment_vals = self._prepare_enrollment_vals(
            form_values, student, activity, start_date, reduced_price)
        try:
            with request.env.cr.savepoint():
                request.env['academy.enrollment'].sudo().create(enrollment_vals)
        except (ValidationError, UserError) as e:
            return self.portal_new_enrollment(
                error=str(e), form_values=form_values)
        except Exception:
            return self.portal_new_enrollment(
                error='An unexpected error occurred while creating the '
                'enrollment.', form_values=form_values)
        return request.redirect('/my/activities/%s' % student.id)

    @route(
        ['/my/student/<int:student_id>'], type='http', auth='user',
        website=True)
    def portal_student_edit(
            self, student_id, error=None, form_values=None, **kw):
        partner = request.env.user.partner_id
        student = request.env['res.partner'].sudo().search([
            ('id', '=', student_id),
            ('tutor_ids', 'in', partner.id),
            ('is_student', '=', True),
        ], limit=1)
        if not student:
            return request.redirect('/my/students')
        academic_trainings = request.env[
            'academy.academic.training'].search([], order='name asc')
        values = {
            'page_name': 'student_edit',
            'student': student,
            'academic_trainings': academic_trainings,
            'error': error,
            'form_values': form_values or {
                'birthdate_date': (
                    student.birthdate_date.isoformat()
                    if student.birthdate_date else ''),
                'academic_training_id': (
                    student.academic_training_ids.id
                    if student.academic_training_ids else ''),
            },
        }
        return request.render('portal_academy.portal_student_edit', values)

    @route(
        ['/my/student/<int:student_id>/save'], type='http', auth='user',
        website=True)
    def portal_student_edit_save(self, student_id, **post):
        partner = request.env.user.partner_id
        student = request.env['res.partner'].sudo().search([
            ('id', '=', student_id),
            ('tutor_ids', 'in', partner.id),
            ('is_student', '=', True),
        ], limit=1)
        if not student:
            return request.redirect('/my/students')
        birthdate = post.get('birthdate_date')
        academic_training_id = int(post.get('academic_training_id') or 0)
        form_values = {
            'birthdate_date': birthdate,
            'academic_training_id': academic_training_id,
        }
        try:
            with request.env.cr.savepoint():
                student.sudo().write({
                    'birthdate_date': birthdate,
                    'academic_training_ids': [
                        (6, 0, [academic_training_id]),
                    ],
                })
        except (ValidationError, UserError) as e:
            return self.portal_student_edit(
                student_id=student_id, error=str(e), form_values=form_values)
        except Exception:
            return self.portal_student_edit(
                student_id=student_id,
                error='Unexpected error while saving the student information.',
                form_values=form_values)
        return request.redirect('/my/students')

    @route(
        ['/my/activities/<int:student_id>'], type='http', auth='user',
        website=True)
    def portal_student_activities(self, student_id, **kw):
        partner = request.env.user.partner_id
        student = request.env['res.partner'].sudo().search([
            ('id', '=', student_id),
            ('tutor_ids', 'in', partner.id),
            ('is_student', '=', True),
        ], limit=1)
        if not student:
            return request.redirect('/my/students')
        enrollments = request.env['academy.enrollment'].sudo().search([
            ('student_id', '=', student.id),
        ], order='start_date asc')
        values = {
            'page_name': 'activities',
            'student': student,
            'enrollments': enrollments,
            'today': date.today(),
        }
        return request.render(
            'portal_academy.portal_student_activities', values)

    @route(
        ['/my/enrollment/cancel/<int:enrollment_id>'],
        type='http', auth='user', website=True)
    def portal_enrollment_cancel(
            self, enrollment_id, error=None, form_values=None, **kw):
        partner = request.env.user.partner_id
        enrollment = request.env['academy.enrollment'].sudo().search([
            ('id', '=', enrollment_id),
            ('student_id', 'in', partner.student_ids.ids),
        ], limit=1)
        if not enrollment:
            return request.redirect(
                '/my/activities/%s' % enrollment.student_id.id)
        if (enrollment.activity_id.end_date
                and enrollment.activity_id.end_date < date.today()):
            return request.redirect(
                '/my/activities/%s' % enrollment.student_id.id)
        values = {
            'page_name': 'enrollment_cancel',
            'enrollment': enrollment,
            'student': enrollment.student_id,
            'form_values': form_values or {
                'end_date': (
                    enrollment.end_date.isoformat() if enrollment.end_date
                    else ''),
            },
            'error': error,
        }
        return request.render('portal_academy.portal_enrollment_cancel', values)

    @route(
        ['/my/enrollment/<int:enrollment_id>/cancel/submit'],
        type='http', auth='user', website=True)
    def portal_enrollment_cancel_submit(self, enrollment_id, **post):
        partner = request.env.user.partner_id
        enrollment = request.env['academy.enrollment'].sudo().search([
            ('id', '=', enrollment_id),
            ('student_id.tutor_ids', 'in', partner.id),
        ], limit=1)
        if not enrollment:
            return request.redirect(
                '/my/activities/%s' % enrollment.student_id.id)
        if (enrollment.activity_id.end_date
                and enrollment.activity_id.end_date < date.today()):
            return request.redirect(
                '/my/activities/%s' % enrollment.student_id.id)
        end_date_raw = post.get('end_date')
        form_values = {
            'end_date': end_date_raw,
        }
        if not end_date_raw:
            return self.portal_enrollment_cancel(
                enrollment_id=enrollment_id, error='End date is required.',
                form_values=form_values)
        try:
            with request.env.cr.savepoint():
                end_date = fields.Date.from_string(end_date_raw)
        except Exception:
            return self.portal_enrollment_cancel(
                enrollment_id=enrollment_id, error='Invalid date format.',
                form_values=form_values)
        min_date = date.today() + timedelta(days=4)
        if end_date < min_date:
            return self.portal_enrollment_cancel(
                enrollment_id=enrollment_id,
                error='End date cannot be earlier than %s.' % min_date,
                form_values=form_values)
        try:
            with request.env.cr.savepoint():
                enrollment.sudo().write({
                    'end_date': end_date,
                    'state': 'cancel_request',
                })
        except (ValidationError, UserError) as e:
            return self.portal_enrollment_cancel(
                enrollment_id=enrollment_id, error=str(e),
                form_values=form_values)
        except Exception:
            return self.portal_enrollment_cancel(
                enrollment_id=enrollment_id,
                error='An unexpected error occurred while cancelling the '
                'enrollment.', form_values=form_values)
        return request.redirect(f'/my/activities/{enrollment.student_id.id}')

    @route(
        ['/my/bank/new'], type='http', auth='user', website=True)
    def portal_bank_new(self, error=None, form_values=None, **kw):
        partner = request.env.user.partner_id
        values = {
            'page_name': 'bank_new',
            'partner': partner,
            'error': error,
            'form_values': form_values or {},
        }
        return request.render('portal_academy.portal_bank_new', values)

    @route(
        ['/my/bank/new/submit'], type='http', auth='user', website=True)
    def portal_bank_new_submit(self, **post):
        partner = request.env.user.partner_id
        acc_number = post.get('acc_number')
        form_values = {
            'acc_number': acc_number,
            'accept_sepa': post.get('accept_sepa'),
        }
        if not acc_number:
            return self.portal_bank_new(
                error='Account number is required.', form_values=form_values)
        if not form_values['accept_sepa']:
            return self.portal_bank_new(
                error='You must accept the SEPA conditions.',
                form_values=form_values)
        try:
            with request.env.cr.savepoint():
                request.env['res.partner.bank'].sudo().create({
                    'partner_id': partner.id,
                    'acc_number': acc_number,
                })
        except (ValidationError, UserError) as exc:
            return self.portal_bank_new(error=str(exc), form_values=form_values)
        except Exception:
            return self.portal_bank_new(
                error='Unexpected error creating bank account.',
                form_values=form_values)
        return request.redirect('/my/account')

    @route(
        ['/my/bank/<int:bank_id>/delete'],
        type='http', auth='user', website=True)
    def portal_bank_delete(self, bank_id, **kw):
        partner = request.env.user.partner_id
        bank_rec = request.env['res.partner.bank'].sudo().search([
            ('id', '=', bank_id),
            ('partner_id', '=', partner.id),
        ], limit=1)
        if bank_rec:
            bank_rec.active = False
        return request.redirect('/my/account')
