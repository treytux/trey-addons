# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class EduSchedule(models.Model):
    _name = 'edu.schedule'
    _description = 'Schedule'
    _inherit = ['mail.thread']

    name = fields.Char(
        compute='_compute_name',
        string='Name',
        required=True)
    period_id = fields.Many2one(
        comodel_name='edu.period',
        string='Period',
        required=True)
    training_plan_line_id = fields.Many2one(
        comodel_name='edu.training.plan.line',
        string='Training Plan Line',
        required=True)
    day_week = fields.Selection(
        selection=[
            ('monday', 'Monday'),
            ('tuesday', 'Tuesday'),
            ('wednesday', 'Wednesday'),
            ('thursday', 'Thursday'),
            ('friday', 'Friday'),
            ('saturday', 'Saturday'),
            ('sunday', 'Sunday')],
        string='Day Week',
        required=True)
    time_slot_id = fields.Many2one(
        comodel_name='edu.time.slot',
        string='Time Slot',
        required=True)
    active = fields.Boolean(
        string='Active',
        default=True,
        track_visibility='onchange')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id)

    @api.model
    def get_day_week_spanish(self, day_week):
        days_week = {
            'Monday': u'Lunes',
            'Tuesday': u'Martes',
            'Wednesday': u'Miércoles',
            'Thursday': u'Jueves',
            'Friday': u'Viernes',
            'Saturday': u'Sábado',
            'Sunday': u'Domingo'}
        return days_week.get(day_week)

    @api.one
    @api.depends('training_plan_line_id', 'day_week', 'time_slot_id')
    def _compute_name(self):
        day_week = dict(
            self._columns['day_week'].selection).get(self.day_week)
        day_week_value = self.get_day_week_spanish(day_week)
        data = dict(
            training_plan=(
                self.training_plan_line_id.training_plan_id.short_name or ''),
            classroom=(self.training_plan_line_id.classroom_id and
                       self.training_plan_line_id.classroom_id.name or ''),
            day_week=day_week_value or '',
            time_slot=self.time_slot_id.name or '')
        self.name = (
            '%(training_plan)s %(classroom)s - %(day_week)s - %(time_slot)s'
            % data)
