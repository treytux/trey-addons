# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields


class EduWizardSchedule(models.TransientModel):
    _name = 'edu.wizard.schedule'
    _description = 'Wizard Schedule'

    def _get_default_training_plan(self):
        if not self.env.context.get('active_id'):
            return
        return self.env.context['active_id']

    teacher_id = fields.Many2one(
        comodel_name='res.partner',
        string='Teacher',
        default=lambda self: self.env.user.partner_id)
    student_id = fields.Many2one(
        comodel_name='res.partner',
        string='Student',
        default=lambda self: self.env.user.partner_id)
    tutor_student_id = fields.Many2one(
        comodel_name='res.partner',
        string='Student',
        domain='[("tutor_ids.user_ids", "in", [uid])]')
    period_id = fields.Many2one(
        comodel_name='edu.period',
        string='Period',
        required=True)
    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        default=_get_default_training_plan)
    classroom_ids = fields.Many2many(
        comodel_name='edu.training.plan.classroom',
        compute='_compute_classrooms',
        string='Classrooms')
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom')
    schedule_line_ids = fields.One2many(
        comodel_name='edu.wizard.schedule.line',
        inverse_name='wizard_schedule_id',
        string='Lines')
    user_type = fields.Selection(
        selection=[
            ('user', 'User'),
            ('teacher', 'Teacher'),
            ('student', 'Student'),
            ('tutor', 'Tutor'),
        ],
        string='User Type')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id)

    @api.one
    @api.depends('training_plan_id')
    def _compute_classrooms(self):
        if not self.user_type == 'user':
            return
        if not self.training_plan_id:
            return
        training_plan = self.env['edu.training.plan'].browse(
            self.training_plan_id.id)
        classroom_ids = [l.id for l in training_plan.classroom_ids]
        self.classroom_ids = [(6, 0, classroom_ids)]

    @api.model
    def schedule_create_values(self, day_week, line):
        return {
            'period_id': self.period_id.id,
            'training_plan_line_id': line[day_week].id,
            'day_week': day_week,
            'time_slot_id': line.time_slot_id.id,
            'message_follower_ids': False}

    def clean_schedules(self, day_week, line):
        schedule = self.env['edu.schedule']
        training_plan_lines = self.env['edu.training.plan.line'].search(
            [('training_plan_id', '=', line[day_week].training_plan_id.id),
             ('classroom_id', '=', line[day_week].classroom_id.id)])
        training_plan_line_ids = [tpl.id for tpl in training_plan_lines]
        schedules = schedule.search([
            ('period_id', '=', self.period_id.id),
            ('training_plan_line_id', 'in', training_plan_line_ids),
            ('day_week', '=', day_week),
            ('time_slot_id', '=', line.time_slot_id.id)])
        len_total = len(schedules)
        for sch in schedules:
            if len_total > 1:
                sch.unlink()
            len_total -= 1

    @api.model
    def schedule_exist(self, day_week, line):
        schedules = self.env['edu.schedule'].search([
            ('period_id', '=', self.period_id.id),
            ('training_plan_line_id', '=', line[day_week].id),
            ('day_week', '=', day_week),
            ('time_slot_id', '=', line.time_slot_id.id)])
        if schedules:
            return True
        return False

    @api.multi
    def button_save_schedule(self):
        week = [
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
            'sunday']
        for line in self.schedule_line_ids:
            for day in week:
                if getattr(line, day) and not self.schedule_exist(day, line):
                    self.env['edu.schedule'].create(
                        self.schedule_create_values(day, line))
                self.clean_schedules(day, line)
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def button_print(self):
        datas = {'ids': [self.id]}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'education_schedule.wizard_schedule',
            'datas': datas,
            'context': {'report_name': 'education_schedule.wizard_schedule'}}

    @api.multi
    def _search_plan_line_id(self, day_week, time_slot_id, line_ids):
            training_plan_lines = self.env['edu.schedule'].search([
                ('period_id', '=', self.period_id.id),
                ('day_week', '=', day_week),
                ('time_slot_id', '=', time_slot_id),
                ('training_plan_line_id', 'in', line_ids)], order='id DESC')
            if not training_plan_lines:
                return None
            return training_plan_lines[0].training_plan_line_id.id

    @api.multi
    def _get_enrollments(self):
        if self.user_type == 'student':
            enrollments = self.env['edu.enrollment'].search([
                ('state', '=', 'active'),
                ('student_id', '=', self.env.user.partner_id.id)])
            return enrollments
        if self.user_type == 'tutor':
            enrollments = self.env['edu.enrollment'].search([
                ('state', '=', 'active'),
                ('student_id', '=', self.tutor_student_id.id)])
            return enrollments

    @api.multi
    def _search_line_ids(self):
        if self.user_type == 'user':
            if not self.training_plan_id.line_ids:
                return None
            line_ids = [l.id for l in self.training_plan_id.line_ids
                        if l.classroom_id == self.classroom_id]
            return line_ids
        if self.user_type == 'teacher':
            lines = self.env['edu.training.plan.line'].search([
                ('teacher_id', '=', self.teacher_id.id)])
            return [l.id for l in lines]
        if self.user_type in ('student', 'tutor'):
            line_ids = []
            enrollments = self._get_enrollments()
            for enroll in enrollments:
                lines = self.env['edu.training.plan.line'].search([
                    ('training_plan_id', '=', enroll.training_plan_id.id),
                    ('classroom_id', '=', enroll.classroom_id and
                        enroll.classroom_id.id or False)])
                line_ids = line_ids + [l.id for l in lines]
            return line_ids

    @api.multi
    def _get_lines(self, time_slots, line_ids):
        lines = [(0, 0, {
            'time_slot_id': ts.id,
            'monday': self._search_plan_line_id('monday', ts.id, line_ids),
            'tuesday': self._search_plan_line_id('tuesday', ts.id, line_ids),
            'wednesday': self._search_plan_line_id(
                'wednesday', ts.id, line_ids),
            'thursday': self._search_plan_line_id('thursday', ts.id, line_ids),
            'friday': self._search_plan_line_id('friday', ts.id, line_ids),
            'saturday': self._search_plan_line_id('saturday', ts.id, line_ids),
            'sunday': self._search_plan_line_id('sunday', ts.id, line_ids)})
            for ts in time_slots]
        return lines

    @api.onchange('tutor_student_id')
    def _onchange_tutor_student_id(self):
        self.period_id = False

    @api.onchange('classroom_id')
    def _onchange_classroom_id(self):
        if self.user_type == 'user':
            if not self.classroom_id or not self.period_id:
                return
            time_slots = self.env['edu.time.slot'].search(
                [('id', 'in', [
                    ts.id for ts in self.classroom_id.time_slot_ids])],
                order='sequence')
            line_ids = self._search_line_ids()
            self.schedule_line_ids = self._get_lines(time_slots, line_ids)

    @api.onchange('period_id')
    def _onchange_period_id(self):
        if not self.period_id:
            return
        line_ids = self._search_line_ids()
        if self.user_type == 'user':
            if not self.classroom_id:
                return
            time_slots = self.env['edu.time.slot'].search(
                [('id', 'in', [
                    ts.id for ts in self.classroom_id.time_slot_ids])],
                order='sequence')
            self.schedule_line_ids = self._get_lines(time_slots, line_ids)
        if self.user_type == 'teacher':
            tp_lines = self.env['edu.training.plan.line'].browse(line_ids)
            time_slots = []
            for line in tp_lines:
                time_slots.extend([
                    ts for ts in line.classroom_id.time_slot_ids
                    if ts not in time_slots])
            self.schedule_line_ids = self._get_lines(time_slots, line_ids)
        if self.user_type in ('student', 'tutor'):
            enrollments = self._get_enrollments()
            time_slots = []
            for enroll in enrollments:
                time_slots.extend([
                    ts for ts in enroll.classroom_id.time_slot_ids
                    if ts not in time_slots])
            self.schedule_line_ids = self._get_lines(time_slots, line_ids)


class WizardScheduleLine(models.TransientModel):
    _name = 'edu.wizard.schedule.line'
    _description = 'Wizard Schedule Line'

    wizard_schedule_id = fields.Many2one(
        comodel_name='edu.wizard.schedule',
        string='Schedule')
    time_slot_id = fields.Many2one(
        comodel_name='edu.time.slot',
        string='Time Slot',
        required=True)
    monday = fields.Many2one(
        comodel_name='edu.training.plan.line',
        string='Monday')
    tuesday = fields.Many2one(
        comodel_name='edu.training.plan.line',
        string='Tuesday')
    wednesday = fields.Many2one(
        comodel_name='edu.training.plan.line',
        string='Wednesday')
    thursday = fields.Many2one(
        comodel_name='edu.training.plan.line',
        string='Thursday')
    friday = fields.Many2one(
        comodel_name='edu.training.plan.line',
        string='Friday')
    saturday = fields.Many2one(
        comodel_name='edu.training.plan.line',
        string='Saturday')
    sunday = fields.Many2one(
        comodel_name='edu.training.plan.line',
        string='Sunday')
