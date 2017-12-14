# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.addons.education.tests.test_base import TestBase


class TestSchedule(TestBase):

    def setUp(self):
        super(TestSchedule, self).setUp()
        self.time_slot_01 = self.env['edu.time.slot'].create({
            'name': 'First hour',
            'start_time': 9.00,
            'end_time': 10.00,
            'sequence': 1
        })
        self.time_slot_02 = self.env['edu.time.slot'].create({
            'name': 'Second hour',
            'start_time': 10.00,
            'end_time': 11.00,
            'sequence': 2
        })
        self.time_slot_03 = self.env['edu.time.slot'].create({
            'name': 'Third hour',
            'start_time': 11.00,
            'end_time': 12.00,
            'sequence': 3
        })
        self.time_slot_04 = self.env['edu.time.slot'].create({
            'name': 'Fourth hour',
            'start_time': 12.30,
            'end_time': 13.30,
            'sequence': 4
        })
        self.time_slot_05 = self.env['edu.time.slot'].create({
            'name': 'Fifth hour',
            'start_time': 13.30,
            'end_time': 14.30,
            'sequence': 5
        })
        self.time_slot_06 = self.env['edu.time.slot'].create({
            'name': 'Sixth hour',
            'start_time': 14.30,
            'end_time': 15.30,
            'sequence': 6
        })
        self.period_01 = self.env['edu.period'].create({
            'name': 'Period 1',
            'start_date': '2016-09-15',
            'end_date': '2016-12-22'
        })
        self.schedule_01 = self.env['edu.schedule'].create({
            'name': 'TPL1 - Monday - Fourth hour',
            'period_id': self.period_01.id,
            'training_plan_line_id': self.training_plan_line_01.id,
            'day_week': 'monday',
            'time_slot_id': self.time_slot_04.id
        })
        self.schedule_02 = self.env['edu.schedule'].create({
            'name': 'TPL1 - Wednesday - Second hour',
            'period_id': self.period_01.id,
            'training_plan_line_id': self.training_plan_line_01.id,
            'day_week': 'wednesday',
            'time_slot_id': self.time_slot_02.id
        })
        self.schedule_03 = self.env['edu.schedule'].create({
            'name': 'TPL1 - Thursday - Sixth hour',
            'period_id': self.period_01.id,
            'training_plan_line_id': self.training_plan_line_01.id,
            'day_week': 'thursday',
            'time_slot_id': self.time_slot_01.id
        })
        self.schedule_04 = self.env['edu.schedule'].create({
            'name': 'TPL1 - Friday - First hour',
            'period_id': self.period_01.id,
            'training_plan_line_id': self.training_plan_line_01.id,
            'day_week': 'friday',
            'time_slot_id': self.time_slot_01.id
        })
