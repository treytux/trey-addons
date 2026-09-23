###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request, route


class CustomerPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        if partner.is_student:
            attendance = request.env['edu.attendance.sheet.line']
            bulletin = request.env['edu.marks.bulletin']
            absence_count = attendance.search_count([
                ('student_id', '=', partner.id),
                ('attendance_sheet_id.state', 'not in', ['draft', 'cancelled']),
                ('present', '=', False),
            ])
            bulletin_count = bulletin.search_count([
                ('name', '=', partner.id),
                ('evaluation_line_ids', '!=', False),
            ])
            values.update({
                'absence_count': absence_count,
                'bulletin_count': bulletin_count,
            })
        elif partner.is_tutor:
            student = request.env['res.partner']
            students_count = student.search_count([
                ('tutor_ids', 'in', partner.ids),
            ])
            values.update({
                'students_count': students_count,
            })
        return values

    @route(['/my/students'], type='http', auth='user', website=True)
    def portal_my_students(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        if not partner.is_tutor:
            return request.redirect('/my')
        student = request.env['res.partner']
        domain = [
            ('tutor_ids', 'in', partner.ids),
        ]
        searchbar_sortings = {
            'name': {'label': _('Title'), 'order': 'name'},
        }
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']
        archive_groups = self._get_archive_groups('res.partner', domain)
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        student_count = student.search_count(domain)
        pager = portal_pager(
            url='/my/students',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby
            },
            total=student_count,
            page=page,
            step=self._items_per_page
        )
        students = student.search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_students_history'] = students.ids[:100]
        values.update({
            'date': date_begin,
            'students': students,
            'page_name': 'students',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/students',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render(
            'portal_education.portal_my_students', values)

    @route(
        ['/my/student/<int:student_id>'], type='http', auth='user',
        website=True, csrf=False)
    def portal_my_student(self, student_id, **kw):
        partner = request.env.user.partner_id
        if student_id not in partner.student_ids.ids:
            return request.redirect('/my')
        student = request.env['res.partner'].browse(student_id)
        absence_count = request.env['edu.attendance.sheet.line'].search_count([
            ('student_id', '=', student.id),
            ('attendance_sheet_id.state', 'not in', ['draft', 'cancelled']),
            ('present', '=', False),
            ('training_plan_line_id.state', '=', 'active'),
        ])
        bulletin_count = request.env['edu.marks.bulletin'].search_count([
            ('name', '=', student.id),
        ])
        values = {
            'student': student,
            'absence_count': absence_count,
            'bulletin_count': bulletin_count,
            'page_name': 'students',
        }
        return request.render('portal_education.portal_tutor_student', values)

    @route(
        ['/my/absences-training-lines/',
         '/my/absences-training-lines/<int:student_id>/'],
        type='http', auth='user', website=True)
    def portal_my_absences_training_lines(
            self, student_id=None, training_plan_id=None, page=1,
            date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        if student_id and student_id not in partner.student_ids.ids:
            return request.redirect('/my')
        if not student_id and partner.is_student:
            student_id = partner.id
            values.update({'is_student': True})
        student = request.env['res.partner'].browse(student_id)
        attendances = request.env['edu.attendance.sheet.line'].search([
            ('student_id', '=', student_id),
            ('attendance_sheet_id.state', 'not in', ['draft', 'cancelled']),
            ('present', '=', False),
        ])
        training_lines = attendances.mapped('training_plan_line_id')
        domain = [
            ('id', 'in', training_lines.ids),
            ('state', '=', 'active'),
        ]
        searchbar_sortings = {
            'name': {'label': _('Title'), 'order': 'name'},
        }
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]
        trainings_count = len(training_lines)
        pager = portal_pager(
            url='/my/absences-training-lines',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby
            },
            total=trainings_count,
            page=page,
            step=self._items_per_page
        )
        training_lines = training_lines.search(
            domain, order=sort_order, limit=self._items_per_page,
            offset=pager['offset'])
        request.session['my_absences_history'] = training_lines.ids[:100]
        values.update({
            'date': date_begin,
            'student': student,
            'training_lines': training_lines,
            'page_name': 'absences',
            'pager': pager,
            'default_url': '/my/absences-training-lines',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render(
            'portal_education.portal_my_absences_training_line', values)

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
        attendance = request.env['edu.attendance.sheet.line']
        domain = [
            ('student_id', '=', student_id),
            ('attendance_sheet_id.state', 'not in', ['draft', 'cancelled']),
            ('present', '=', False),
            ('training_plan_line_id', '=', line_id),
        ]
        searchbar_sortings = {
            'name': {'label': _('Title'), 'order': 'date'},
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
                'sortby': sortby
            },
            total=absence_count,
            page=page,
            step=self._items_per_page
        )
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
        return request.render(
            'portal_education.portal_my_absences', values)

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
        bulletin = request.env['edu.marks.bulletin']
        domain = [
            ('name', '=', student_id),
            ('evaluation_line_ids', '!=', False),
        ]
        searchbar_sortings = {
            'name': {'label': _('Title'), 'order': 'year'},
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
                'sortby': sortby
            },
            total=bulletin_count,
            page=page,
            step=self._items_per_page
        )
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
        return request.render(
            'portal_education.portal_my_bulletins', values)

    @route(
        ['/my/evaluations/<int:bulletin_id>'], type='http', auth='user',
        website=True, csrf=False)
    def portal_my_evaluation(self, bulletin_id, **kw):
        partner = request.env.user.partner_id
        evaluations = request.env['edu.evaluation.line'].search([
            ('bulletin_id', '=', bulletin_id),
        ])
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
        return request.render('portal_education.portal_my_evaluations', values)
