###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from collections import OrderedDict
from datetime import datetime, time

import werkzeug.utils as utils
from odoo import _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request, route
from pytz import UTC


class EmployeeWebsite(CustomerPortal):
    def savepoint(self, name):
        request.env.cr.execute('SAVEPOINT %s' % name)

    def rollback(self, name):
        request.env.cr.execute('ROLLBACK TO SAVEPOINT %s' % name)

    def release(self, name):
        request.env.cr.execute('RELEASE SAVEPOINT %s' % name)

    @route()
    def home(self, **kw):
        if request.env.user.employee_portal_block_backoffice:
            return request.redirect('/employee')
        else:
            return super().home(**kw)

    def get_employee(self):
        employee = request.env.user.employee_ids
        if not employee:
            return False
        return employee[0]

    def get_allowed_categories(self, knowledge_categories):
        allowed_categories = knowledge_categories.ids
        child_ids = [
            kc.child_ids.ids for kc in knowledge_categories]
        for child_id in child_ids:
            allowed_categories += child_id
        return allowed_categories

    @route('/employee', type='http', auth='user', website=True)
    def portal_employee(self, **kw):
        error = kw.get('error', False)
        if int(error) == 1:
            error = _('You must be linked to an employee')
        values = {
            'error': error,
        }
        return request.render('portal_employee.portal_employee', values)

    @route([
        '/employee/knowledge',
        '/employee/knowledge/category/<int:category>',
    ],
        type='http', auth='user', website=True)
    def portal_employee_knowledge(self, category=None, **kw):
        employee = self.get_employee()
        if not employee:
            return utils.redirect('/')
        knowledge_categories = request.env.user.knowledge_categories
        if not category:
            domain = [
                ('id', 'in', request.env.user.knowledge_categories.ids),
                ('type', '=', 'category'),
            ]
            categories = request.env['document.page'].search(
                domain, order='sequence asc, name asc')
        else:
            allowed_categories = self.get_allowed_categories(
                knowledge_categories)
            if category not in allowed_categories:
                return utils.redirect('/my')
            parent_id = category and category or None
            domain = [
                ('id', 'in', allowed_categories),
                ('parent_id', '=', parent_id),
                ('type', '=', 'category'),
            ]
            categories = request.env['document.page'].search(
                domain, order='sequence asc, name asc')
        documents = []
        current_category = (
            category and request.env['document.page'].browse(category) or None)
        if category and category in allowed_categories and not categories:
            domain = [
                ('parent_id', '=', parent_id),
                ('type', '!=', 'category'),
            ]
            documents = request.env['document.page'].search(
                domain, order='sequence asc, name asc')
        values = {
            'categories': categories,
            'current_category': current_category,
            'documents': documents,
            'default_url': '/employee/knowledge',
            'employee': employee,
            'page_name': 'knowledge',
        }
        return request.render(
            'portal_employee.portal_employee_knowledge', values)

    @route([
        '/employee/knowledge/document/<int:page_id>'],
        type='http', auth='user', website=True)
    def portal_employee_knowledge_page(
            self, page_id, **kw):
        employee = self.get_employee()
        if not employee:
            return utils.redirect('/')
        page = request.env['document.page'].browse(
            page_id)
        if not page or page.type != 'content':
            return utils.redirect('/knowledge')
        allowed_categories = self.get_allowed_categories(
            request.env.user.knowledge_categories)
        if page.parent_id and page.parent_id.id not in allowed_categories:
            return utils.redirect('/my')
        values = {
            'employee': employee,
            'page': page,
            'page_name': 'knowledge_page',
        }
        return request.render(
            'portal_employee.portal_employee_knowledge_page', values)

    @route([
        '/employee/knowledge/attachment/download/<int:document_id>/'
        '<int:attachment_id>'],
        type='http', auth='user', website=True)
    def portal_employee_knowledge_attachment_download(
            self, document_id, attachment_id):
        employee = self.get_employee()
        if not employee:
            return utils.redirect('/')
        document = request.env['document.page'].browse(document_id)
        if not document:
            return utils.redirect('/my')
        attachment = request.env['ir.attachment'].browse(attachment_id)
        if not attachment:
            return utils.redirect('/my')
        allowed_categories = self.get_allowed_categories(
            request.env.user.knowledge_categories)
        if (
            document.parent_id and document.parent_id.id
                not in allowed_categories):
            return utils.redirect('/my')
        name = attachment.name
        disposition = 'attachment; filename=%s' % name
        httpheaders = [
            ('Content-Type', attachment.mimetype),
            ('Content-Length', len(attachment.datas)),
            ('Content-Disposition', disposition)
        ]
        content_base64 = base64.b64decode(attachment.datas)
        return request.make_response(content_base64, headers=httpheaders)

    def get_check_in_state(self):
        employee = self.get_employee()
        if not employee:
            return utils.redirect('/')
        attendance_state = employee.attendance_state
        return False if attendance_state == 'checked_in' else True

    def get_attendances(self, id, limit=False, offset=False):
        if limit:
            return request.env['hr.attendance'].search([
                ('employee_id', '=', id)
            ], limit=limit, offset=offset)
        else:
            return request.env['hr.attendance'].search([
                ('employee_id', '=', id)
            ])

    @route('/employee/attendance/change-state', type='http', auth='user',
           website='True')
    def change_state(self):
        employee = self.get_employee()
        if not employee:
            return utils.redirect('/')
        check_in_state = self.get_check_in_state()
        if check_in_state:
            request.env['hr.attendance'].create({
                'employee_id': employee.id,
                'check_in': datetime.now()
            })
        else:
            attendance = employee.last_attendance_id
            attendance.check_out = datetime.now()
        return utils.redirect('employee/attendances')

    @route(
        ['/employee/attendances', '/employee/attendances/page/<int:page>'],
        type='http', auth='user', website=True)
    def portal_employee_attendance(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        employee = self.get_employee()
        if not employee:
            return utils.redirect('/')
        module = 'portal_employee'
        template = 'portal_employee_attendance'
        attendances = self.get_attendances(employee.id)
        attendance_count = len(attendances)
        pager = portal_pager(
            url='/employee/attendances',
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby
            },
            total=attendance_count,
            page=page,
            step=self._items_per_page
        )
        attendances = self.get_attendances(
            employee.id, self._items_per_page, pager['offset'])
        check_in_state = self.get_check_in_state()
        values = {
            'date': date_begin,
            'attendances': attendances,
            'page_name': 'attendance',
            'check_in_state': check_in_state,
            'pager': pager,
            'default_url': '/employee/attendances',
        }
        return request.render(f'{module}.{template}', values)

    def get_leave_states(self):
        return {
            'draft': 'info',
            'cancel': 'danger',
            'confirm': 'info',
            'refuse': 'danger',
            'validate1': 'warning',
            'validate': 'success',
        }

    def portal_employee_leaves(
            self, page=False, date_begin=False, date_end=False,
            sortby=False, filterby=False, kw=False, leave_type=False,
            page_name=False, default_url=False, template=False):
        employee = self.get_employee()
        if not employee:
            return utils.redirect('/')
        leave_states = self.get_leave_states()
        holidays_type = request.env.user.company_id.holidays_type
        absences_type = request.env.user.company_id.absences_type
        domain = [
            ('employee_id', '=', employee.id),
        ]
        holiday_status_ids = (
            leave_type == 'holidays' and holidays_type.ids or absences_type.ids)
        domain += [
            ('holiday_status_id', 'in', holiday_status_ids),
        ]
        searchbar_sortings = {
            'date_desc': {'label': _('Newest'), 'order': 'date_from desc'},
            'date_asc': {'label': _('Oldest'), 'order': 'date_from asc'},
        }
        searchbar_filters = {
            'all': {
                'label': _('All'),
                'domain': []
            },
            'pending': {
                'label': _('Pending'),
                'domain': [('state', '=', 'confirm')]
            },
            'refuse': {
                'label': _('Refuse'),
                'domain': [('state', '=', 'refuse')]
            },
            'approved': {
                'label': _('Approved'),
                'domain': [('state', '=', 'validate')]
            }
        }
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        if not sortby:
            sortby = 'date_desc'
        order = searchbar_sortings[sortby]['order']
        leaves_count = len(request.env['hr.leave'].search(domain))
        pager = portal_pager(
            url=default_url,
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
                'filterby': filterby,
            },
            total=leaves_count,
            page=page,
            step=self._items_per_page,
        )
        leaves = request.env['hr.leave'].search(
            domain, order=order, limit=self._items_per_page,
            offset=pager['offset'])
        values = {
            'date': date_begin,
            'leave_states': leave_states,
            'leaves': leaves,
            'page_name': page_name,
            'pager': pager,
            'default_url': default_url,
            'filterby': filterby,
            'sortby': sortby,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items()))
        }
        return request.render(template, values)

    @route(['/employee/holidays', '/employee/holidays/page/<int:page>'],
           type='http', auth='user', website=True)
    def portal_employee_holidays(
            self, page=1, date_begin=None, date_end=None, sortby=None,
            filterby=None, **kw):
        return self.portal_employee_leaves(
            page=page, date_begin=date_begin, date_end=date_end,
            sortby=sortby, filterby=filterby, kw=kw,
            leave_type='holidays',
            default_url='/employee/holidays',
            page_name='holidays',
            template='portal_employee.portal_employee_holidays')

    @route(['/employee/absences', '/employee/absences/page/<int:page>'],
           type='http', auth='user', website=True)
    def portal_employee_absences(
            self, page=1, date_begin=None, date_end=None, sortby=None,
            filterby=None, **kw):
        return self.portal_employee_leaves(
            page=page, date_begin=date_begin, date_end=date_end,
            sortby=sortby, filterby=filterby, kw=kw,
            leave_type='absences',
            default_url='/employee/absences',
            page_name='absences',
            template='portal_employee.portal_employee_absences')

    def leave_check_holidays(
            self, employee, start_date, end_date, leave_type_id):
        leaves_report = request.env['hr.leave.report'].search([
            ('employee_id', '=', employee.id),
            ('holiday_status_id.id', '=', leave_type_id),
        ])
        employee_days = 0
        for leave in leaves_report.mapped('number_of_days'):
            leave = int(leave)
            if leave > 0:
                employee_days += leave
            else:
                employee_days -= abs(leave)
        start_date_time = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_time = datetime.strptime(end_date, '%Y-%m-%d')
        if (end_date_time - start_date_time).days > employee_days:
            return False
        return True

    def leave_check_date(
            self, employee, request_date_from, request_date_to):
        leaves = request.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('date_from', '>=', datetime.strptime(
                request_date_from, '%Y-%m-%d')),
            ('date_to', '<=', datetime.strptime(request_date_to, '%Y-%m-%d')),
            ('state', 'in', ['confirm', 'validate']),
        ])
        return not leaves and True or False

    def validate_leave_request(self, employee, kw):
        errors = []
        request_date_from = kw.get('request_date_from', '')
        request_date_to = kw.get('request_date_to', '')
        leave_type_id = kw.get('leave_type_id', False)
        leave_type_id = leave_type_id and int(leave_type_id) or leave_type_id
        if not leave_type_id:
            errors.append('Missing holidays type.')
        if leave_type_id and not self.leave_check_holidays(
                employee, request_date_from, request_date_to, leave_type_id):
            errors.append('You don\'t have enought days.')
        if not self.leave_check_date(
                employee, request_date_from, request_date_to):
            errors.append(
                'You can not have 2 leaves that overlaps on the same day.')
        return errors

    def portal_employee_leave_request(
            self, id=False, kw=False, page_name=False, leave_type=False,
            redirect_url=False, template=False):
        employee = self.get_employee()
        if not employee:
            return utils.redirect('/')
        values = {
            'employee_id': employee.id,
            'errors': [],
            'leave': False,
            'page_name': page_name,
        }
        leave = id and request.env['hr.leave'].search([
            ('id', '=', id),
            ('employee_id', '=', employee.id),
        ]) or False
        if leave:
            original_data = {
                'employee_id': leave.employee_id.id,
                'holiday_status_id': leave.holiday_status_id.id,
                'name': leave.name,
                'request_date_from': leave.request_date_from,
                'request_date_to': leave.request_date_to,
                'date_from': leave.date_from,
                'date_to': leave.date_to,
            }
            values['leave'] = leave
            values['selected_holiday_status_id'] = leave.holiday_status_id.id
        else:
            values['selected_holiday_status_id'] = kw.get(
                'holiday_status_id', False)
        if request.httprequest.method == 'POST':
            datetime_from = datetime.combine(
                datetime.strptime(
                    kw.get('request_date_from'), '%Y-%m-%d'), time.min
            ).astimezone(UTC)
            datetime_to = datetime.combine(
                datetime.strptime(
                    kw.get('request_date_to'), '%Y-%m-%d'), time.max
            ).astimezone(UTC)
            data = {
                'employee_id': employee.id,
                'holiday_status_id': int(kw.get('holiday_status_id')),
                'name': kw.get('name'),
                'request_date_from': datetime_from,
                'request_date_to': datetime_to,
                'date_from': datetime_from,
                'date_to': datetime_to,
            }
            start_time_str = kw.get('start_time')
            end_time_str = kw.get('end_time')
            if start_time_str and end_time_str:
                hours_from, minutes_from = [
                    int(value) for value in kw.get('start_time').split(':')]
                hours_to, minutes_to = [
                    int(value) for value in kw.get('end_time').split(':')]
                data.update({
                    'request_date_to': False,
                    'request_unit_hours': True,
                    'request_hour_from': (
                        minutes_from and -(hours_from + 1) or hours_from),
                    'request_hour_to': (
                        minutes_to and -(hours_to + 1) or hours_to),
                })
            try:
                self.savepoint('save_leave')
                if leave:
                    leave.write(data)
                else:
                    leave = request.env['hr.leave'].create(data)
                leave._onchange_request_parameters()
            except Exception as e:
                self.rollback('save_leave')
                if getattr(e, 'name', None):
                    values['errors'].append(e.name)
                elif getattr(e, 'pgerror', None):
                    if 'constraint' in e.pgerror:
                        values['errors'].append(
                            'Check request data.')
                    else:
                        values['errors'].append(e.pgerror)
                else:
                    values['errors'].append(e.args[0])
            else:
                self.release('save_leave')
                return request.redirect(redirect_url)
            values.update(data)
        else:
            if leave:
                data = original_data
                values.update(data)
        leave_types = (
            leave_type == 'holidays'
            and request.env.user.company_id.holidays_type
            or request.env.user.company_id.absences_type)
        values['leave_types'] = leave_types
        return request.render(template, values)

    @route([
        '/employee/holidays/request',
        '/employee/holidays/request/<int:id>',
    ], type='http', methods=['GET', 'POST'], auth='user', website=True)
    def portal_employee_holidays_request(self, id=False, **kw):
        return self.portal_employee_leave_request(
            id=id, kw=kw, redirect_url='/employee/holidays',
            page_name='holidays_request',
            leave_type='holidays',
            template='portal_employee.portal_employee_holidays_request')

    @route([
        '/employee/absences/request',
        '/employee/absences/request/<int:id>',
    ], type='http', methods=['GET', 'POST'], auth='user', website=True)
    def portal_employee_absences_request(self, id=False, **kw):
        return self.portal_employee_leave_request(
            id=id, kw=kw, redirect_url='/employee/absences',
            page_name='absences_request',
            leave_type='absences',
            template='portal_employee.portal_employee_absences_request')
