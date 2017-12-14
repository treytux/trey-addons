# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api
from functools import partial
import datetime


class EducationEduEnrollment(models.TransientModel):
    _name = 'report.education.edu_enrollment'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        enrollment_obj = self.env['edu.enrollment']
        report = report_obj._get_report_from_name('education.edu_enrollment')
        enrollments = enrollment_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': enrollments}
        report = report_obj.browse(self.ids[0])
        return report.render('education.edu_enrollment', docargs)


class EducationReceipt(models.TransientModel):
    _name = 'report.education.receipt'

    @api.multi
    def get_day_week(self):
        today = datetime.datetime.today()
        day_week = today.weekday()
        week_day_dict = {
            0: 'lunes',
            1: 'martes',
            2: u'miércoles',
            3: 'jueves',
            4: 'viernes',
            5: 'sábado',
            6: 'domingo'}
        return week_day_dict[day_week]

    @api.multi
    def get_month(self):
        today = datetime.datetime.today()
        month = today.month
        month_dict = {
            1: 'enero',
            2: 'febrero',
            3: 'marzo',
            4: 'abril',
            5: 'mayo',
            6: 'junio',
            7: 'julio',
            8: 'agosto',
            9: 'septiembre',
            10: 'octubre',
            11: 'noviembre',
            12: 'diciembre'}
        return month_dict[month]

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('education.receipt')
        training_plan = False
        classroom = False
        bank = False
        active_ids = self.ids
        if data and data.get('training_plan_id'):
            training_plan_id = data.get('training_plan_id')[0]
            training_plan = self.env['edu.training.plan'].browse(
                training_plan_id)
        if data and data.get('classroom_id'):
            classroom_id = data.get('classroom_id')[0]
            classroom = self.env[
                'edu.training.plan.classroom'].browse(classroom_id)
        if data and data.get('bank_id'):
            bank_id = data.get('bank_id')[0]
            bank = self.env['res.partner.bank'].browse(bank_id)
        if data and data.get('active_ids'):
            active_ids = data.get('active_ids')
        docs = self.env['res.partner'].browse(active_ids)
        docargs = {
            'doc_model': report.model,
            'training_plan_id': training_plan,
            'classroom_id': classroom,
            'receipt_description': data and data.get(
                'receipt_description') or False,
            'receipt_amount': data and data.get('receipt_amount') or False,
            'bank_id': bank,
            'get_day_week': partial(self.get_day_week),
            'get_month': partial(self.get_month),
            'doc_ids': active_ids,
            'docs': docs}
        report = report_obj.browse(report.id)
        return report.render('education.receipt', docargs)
