###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from collections import OrderedDict
from datetime import datetime, time

from odoo import _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import UserError
from odoo.http import request, route


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
        employees = request.env['hr.employee'].sudo().search([(
            'user_id', '=', request.env.user.id)])
        if not employees:
            return False
        return employees[0]

    def get_allowed_categories(self, knowledge_categories):
        knowledge_categories = knowledge_categories.sudo()
        allowed_categories = knowledge_categories.ids
        child_ids = [kc.child_ids.ids for kc in knowledge_categories]
        for child_id in child_ids:
            allowed_categories += child_id
        return allowed_categories

    def _get_employee_knowledge_company_ids(self, employee):
        companies = employee.company_id.sudo()
        parent = companies.parent_id
        while parent:
            companies |= parent
            parent = parent.parent_id
        return companies.ids

    def _get_employee_knowledge_company_domain(self, employee):
        return [
            '|',
            ('company_id', '=', False),
            ('company_id', 'in', self._get_employee_knowledge_company_ids(
                employee)),
        ]

    def _is_employee_knowledge_company_allowed(self, record, employee):
        if not record.company_id:
            return True
        return record.company_id.id in self._get_employee_knowledge_company_ids(
            employee)

    def _check_employee_knowledge_page_access(self, page_id):
        employee = self.get_employee()
        if not employee:
            return False
        page = request.env['document.page'].sudo().browse(page_id).exists()
        if not page or page.type != 'content':
            return False
        if not self._is_employee_knowledge_company_allowed(page, employee):
            return False
        if (
            page.parent_id
            and not self._is_employee_knowledge_company_allowed(
                page.parent_id, employee)
        ):
            return False
        allowed_categories = self.get_allowed_categories(
            request.env.user.knowledge_categories)
        if page.parent_id and page.parent_id.id not in allowed_categories:
            return False
        return page.sudo()

    @route('/employee', type='http', auth='user', website=True)
    def portal_employee(self, **kw):
        error = kw.get('error', False)
        if error and str(error) == '1':
            error = _('You must be linked to an employee')
        values = {
            'error': error,
        }
        return request.render('portal_employee.portal_employee', values)

    @route([
        '/employee/knowledge',
        '/employee/knowledge/category/<int:category>',
    ], type='http', auth='user', website=True)
    def portal_employee_knowledge(self, category=None, **kw):
        employee = self.get_employee()
        if not employee:
            return request.redirect('/')
        page_obj = request.env['document.page'].sudo()
        knowledge_categories = request.env.user.sudo().knowledge_categories
        company_domain = self._get_employee_knowledge_company_domain(employee)
        if not category:
            domain = [
                ('id', 'in', knowledge_categories.ids),
                ('type', '=', 'category'),
            ] + company_domain
            categories = page_obj.search(domain, order='name asc')
        else:
            allowed_categories = self.get_allowed_categories(
                knowledge_categories)
            current_category = page_obj.browse(category).exists()
            if (
                category not in allowed_categories
                or not current_category
                or not self._is_employee_knowledge_company_allowed(
                    current_category, employee)
            ):
                return request.redirect('/my')
            parent_id = category or None
            domain = [
                ('id', 'in', allowed_categories),
                ('parent_id', '=', parent_id),
                ('type', '=', 'category'),
            ] + company_domain
            categories = page_obj.search(domain, order='name asc')
        documents = []
        current_category = (
            category and page_obj.browse(category) or None)
        if (
            category
            and category in self.get_allowed_categories(knowledge_categories)
            and not categories
        ):
            parent_search = category or None
            domain = [
                ('parent_id', '=', parent_search),
                ('type', '!=', 'category'),
            ] + company_domain
            documents = page_obj.search(domain, order='name asc')

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
    def portal_employee_knowledge_page(self, page_id, **kw):
        page = self._check_employee_knowledge_page_access(page_id)
        if not page:
            return request.redirect('/knowledge')
        values = {
            'employee': self.get_employee(),
            'page': page,
            'page_name': 'knowledge_page',
        }
        return request.render(
            'portal_employee.portal_employee_knowledge_page', values)

    @route(
        '/employee/knowledge/document/<int:page_id>/sign',
        type='json', auth='user', website=True)
    def portal_employee_knowledge_document_sign(
            self, page_id, name=None, signature=None):
        page = self._check_employee_knowledge_page_access(page_id)
        if not page:
            return {'error': _('You cannot sign this document.')}
        try:
            page.action_sign_pdf_attachment(name, signature)
        except UserError as error:
            return {'error': error.args[0]}
        return {
            'success': True,
            'force_refresh': True,
        }

    @route([
        '/employee/knowledge/attachment/download'
        '/<int:document_id>/<int:attachment_id>'],
        type='http', auth='user', website=True)
    def portal_employee_knowledge_attachment_download(
            self, document_id, attachment_id):
        document = self._check_employee_knowledge_page_access(document_id)
        if not document:
            return request.redirect('/my')
        attachment = request.env['ir.attachment'].sudo().browse(
            attachment_id).exists()
        if not attachment:
            return request.redirect('/my')
        if (
            attachment.res_model != 'document.page'
            or attachment.res_id != document.id
        ):
            return request.redirect('/my')
        name = attachment.name
        content_base64 = base64.b64decode(attachment.datas)
        headers = [
            ('Content-Type', attachment.mimetype),
            ('Content-Length', len(content_base64)),
            ('Content-Disposition', f'attachment; filename={name}')
        ]
        return request.make_response(content_base64, headers=headers)

    def get_check_in_state(self):
        employee = self.get_employee()
        if not employee:
            return True
        attendance_state = employee.attendance_state
        return False if attendance_state == 'checked_in' else True

    def get_attendances(self, emp_id, limit=False, offset=False):
        domain = [('employee_id', '=', emp_id)]
        if limit:
            return request.env['hr.attendance'].search(
                domain, limit=limit, offset=offset)
        else:
            return request.env['hr.attendance'].search(domain)

    @route('/employee/attendance/change-state', type='http', auth='user', website=True)
    def change_state(self):
        employee = self.get_employee()
        if not employee:
            return request.redirect('/')
        check_in_state = self.get_check_in_state()
        if check_in_state:
            request.env['hr.attendance'].create({
                'employee_id': employee.id,
                'check_in': datetime.now()
            })
        else:
            attendance = employee.last_attendance_id
            if attendance:
                attendance.check_out = datetime.now()
        return request.redirect('/employee/attendances')

    @route(['/employee/attendances', '/employee/attendances/page/<int:page>'],
           type='http', auth='user', website=True)
    def portal_employee_attendance(self, page=1, date_begin=None,
                                   date_end=None, sortby=None, **kw):
        employee = self.get_employee()
        if not employee:
            return request.redirect('/')
        module = 'portal_employee'
        template = 'portal_employee_attendance'
        attendances_all = self.get_attendances(employee.id)
        attendance_count = len(attendances_all)
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

    def portal_employee_leaves(self, page=False, date_begin=False, date_end=False,
                               sortby=False, filterby=False, kw=False, leave_type=False,
                               page_name=False, default_url=False, template=False):
        employee = self.get_employee()
        if not employee:
            return request.redirect('/')
        leave_states = self.get_leave_states()
        holidays_type = request.env.user.company_id.holidays_type
        absences_type = request.env.user.company_id.absences_type
        domain = [('employee_id', '=', employee.id)]
        if leave_type == 'holidays':
            holiday_status_ids = holidays_type.ids
        else:
            holiday_status_ids = absences_type.ids
        domain += [('holiday_status_id', 'in', holiday_status_ids)]
        searchbar_sortings = {
            'date_desc': {'label': _('Newest'), 'order': 'date_from desc'},
            'date_asc': {'label': _('Oldest'), 'order': 'date_from asc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'pending': {'label': _('Pending'), 'domain': [('state', '=', 'confirm')]},
            'refuse': {'label': _('Refuse'), 'domain': [('state', '=', 'refuse')]},
            'approved': {'label': _('Approved'), 'domain': [('state', '=', 'validate')]}
        }
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        if not sortby:
            sortby = 'date_desc'
        order = searchbar_sortings[sortby]['order']
        leaves_count = request.env['hr.leave'].search_count(domain)
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
    def portal_employee_holidays(self, page=1, date_begin=None, date_end=None,
                                 sortby=None, filterby=None, **kw):
        return self.portal_employee_leaves(
            page=page, date_begin=date_begin, date_end=date_end,
            sortby=sortby, filterby=filterby, kw=kw,
            leave_type='holidays',
            default_url='/employee/holidays',
            page_name='holidays',
            template='portal_employee.portal_employee_holidays')

    @route(['/employee/absences', '/employee/absences/page/<int:page>'],
           type='http', auth='user', website=True)
    def portal_employee_absences(self, page=1, date_begin=None, date_end=None,
                                 sortby=None, filterby=None, **kw):
        return self.portal_employee_leaves(
            page=page, date_begin=date_begin, date_end=date_end,
            sortby=sortby, filterby=filterby, kw=kw,
            leave_type='absences',
            default_url='/employee/absences',
            page_name='absences',
            template='portal_employee.portal_employee_absences')

    def leave_check_holidays(self, employee, start_date, end_date, leave_type_id):
        leaves_report = request.env['hr.leave.report'].search([
            ('employee_id', '=', employee.id),
            ('holiday_status_id.id', '=', leave_type_id),
            ('state', '=', 'validate'),
        ])
        employee_days = 0
        for leave in leaves_report:
            days = leave.number_of_days
            if days > 0:
                employee_days += days
            else:
                employee_days -= abs(days)
        start_date_time = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_time = datetime.strptime(end_date, '%Y-%m-%d')
        requested_days = (end_date_time - start_date_time).days
        if requested_days > employee_days:
            return False
        return True

    def leave_check_date(self, employee, request_date_from, request_date_to):
        domain = [
            ('employee_id', '=', employee.id),
            ('date_from', '<', request_date_to),
            ('date_to', '>', request_date_from),
            ('state', 'in', ['confirm', 'validate']),
        ]
        count = request.env['hr.leave'].search_count(domain)
        return count == 0

    def portal_employee_leave_request(self, id=False, kw=False, page_name=False,
                                      leave_type=False, redirect_url=False,
                                      template=False):
        employee = self.get_employee()
        if not employee:
            return request.redirect('/')
        values = {
            'employee_id': employee.id,
            'errors': [],
            'leave': False,
            'page_name': page_name,
        }
        leave = False
        if id:
            leave = request.env['hr.leave'].search([
                ('id', '=', id),
                ('employee_id', '=', employee.id),
            ])
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
            values['selected_holiday_status_id'] = kw.get('holiday_status_id', False)
            if values['selected_holiday_status_id']:
                values['selected_holiday_status_id'] = int(
                    values['selected_holiday_status_id'])
        if request.httprequest.method == 'POST':
            try:
                req_date_from_str = kw.get('request_date_from')
                req_date_to_str = kw.get('request_date_to')
                dt_from = datetime.combine(
                    datetime.strptime(req_date_from_str, '%Y-%m-%d'), time.min
                )
                dt_to = datetime.combine(
                    datetime.strptime(req_date_to_str, '%Y-%m-%d'), time.max
                )
                data = {
                    'employee_id': employee.id,
                    'holiday_status_id': int(kw.get('holiday_status_id')),
                    'name': kw.get('name'),
                    'request_date_from': dt_from.date(),
                    'request_date_to': dt_to.date(),
                    'date_from': dt_from,
                    'date_to': dt_to,
                }
                start_time_str = kw.get('start_time')
                end_time_str = kw.get('end_time')
                if start_time_str and end_time_str:
                    hours_from, minutes_from = map(int, start_time_str.split(':'))
                    hours_to, minutes_to = map(int, end_time_str.split(':'))
                    data.update({
                        'request_unit_hours': True,
                        'request_hour_from': str(
                            hours_from + (minutes_from / 60.0)
                            if minutes_from else hours_from
                        ),
                        'request_hour_to': str(
                            hours_to + (minutes_to / 60.0)
                            if minutes_to else hours_to
                        ),
                    })
                self.savepoint('save_leave')
                if leave:
                    leave.write(data)
                else:
                    leave = request.env['hr.leave'].create(data)
                leave._compute_date_from_to()
            except Exception as e:
                self.rollback('save_leave')
                error_msg = str(e)
                if hasattr(e, 'name'):
                    error_msg = e.name
                elif hasattr(e, 'pgerror'):
                    if 'constraint' in (e.pgerror or ''):
                        error_msg = _('Check request data (overlap or constraints).')
                    else:
                        error_msg = e.pgerror
                values['errors'].append(error_msg)
                values.update(data)
            else:
                self.release('save_leave')
                return request.redirect(redirect_url)
        else:
            if leave:
                values.update(original_data)
        if leave_type == 'holidays':
            leave_types = request.env.user.company_id.holidays_type
        else:
            leave_types = request.env.user.company_id.absences_type

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
