###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo import Command
from odoo.tests.common import TransactionCase


class TestBase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.manager_01 = self.env.ref('academy.user_manager_01')
        self.state_01 = self.env.ref('base.state_es_gr')
        self.teacher_01 = self.env['hr.employee'].create({
            'name': 'Teacher 01',
            'work_email': 'teacher_01@test.com',
            'work_phone': '958010203',
        })
        self.teacher_02 = self.env['hr.employee'].create({
            'name': 'Teacher 02',
            'work_email': 'teacher_02@test.com',
            'work_phone': '958010203',
        })
        self.mother_01 = self.env['res.partner'].create({
            'name': 'Mother 01',
            'is_tutor': True,
            'email': 'mother_01@test.com',
            'street': 'Street, 1',
            'street2': 'Street2, 1',
            'city': 'City 1',
            'zip': '18001',
            'state_id': self.state_01.id,
            'country_id': self.env['res.country'].search([
                ('code', '=', 'ES'),
            ]).id,
            'phone': '958010203',
        })
        self.father_01 = self.env['res.partner'].create({
            'name': 'Father 01',
            'is_tutor': True,
            'email': 'Father_01@test.com',
            'street': 'Street, 1',
            'street2': 'Street2, 1',
            'city': 'City 1',
            'zip': '18001',
            'state_id': self.state_01.id,
            'country_id': self.env['res.country'].search([
                ('code', '=', 'ES'),
            ]).id,
            'phone': '958010203',
        })
        academy_academic_training_obj = self.env['academy.academic.training']
        self.academic_training_01 = academy_academic_training_obj.create({
            'name': 'A1',
        })
        self.academic_training_02 = academy_academic_training_obj.create({
            'name': 'B1',
        })
        self.student_01 = self.env['res.partner'].create({
            'name': 'Student 01',
            'tutor_ids': [Command.set(self.mother_01.ids)],
            'academic_training_ids': [
                Command.set(self.academic_training_01.ids)],
            'is_student': True,
            'email': 'student_01@test.com',
            'street': 'Street Street Street Street Street Street, 1',
            'street2': 'Street2, 1',
            'city': 'City 1',
            'zip': '18001',
            'state_id': self.state_01.id,
            'country_id': self.env['res.country'].search([
                ('code', '=', 'ES'),
            ]).id,
            'phone': '958010203',
        })
        self.student_02 = self.env['res.partner'].create({
            'name': 'Student 02',
            'tutor_ids': [Command.set(self.father_01.ids)],
            'academic_training_ids': [
                Command.set(self.academic_training_02.ids)],
            'is_student': True,
            'email': 'student_02@test.com',
            'street': 'Street Street Street Street Street Street, 1',
            'street2': 'Street2, 1',
            'city': 'City 1',
            'zip': '18001',
            'state_id': self.state_01.id,
            'country_id': self.env['res.country'].search([
                ('code', '=', 'ES'),
            ]).id,
            'phone': '958010204',
        })
        self.training_plan_01 = self.env['academy.training.plan'].create({
            'name': 'Trainig Plan 01',
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=31, month=12),
            'user_id': self.manager_01.id,
            'description': '''
            Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean
            commodo ligula eget dolor. Aenean massa. Cum sociis natoque
            penatibus et magnis dis parturient montes, nascetur ridiculus mus.
            Donec quam felis, ultricies nec, pellentesque eu, pretium quis,
            sem.
            ''',
        })
        self.training_plan_02 = self.env['academy.training.plan'].create({
            'name': 'Trainig Plan 02',
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=31, month=12),
            'user_id': self.manager_01.id,
            'description': '''
            Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean
            commodo ligula eget dolor. Aenean massa. Cum sociis natoque
            penatibus et magnis dis parturient montes, nascetur ridiculus mus.
            Donec quam felis, ultricies nec, pellentesque eu, pretium quis,
            sem.
            ''',
        })
        self.evaluation_01 = self.env['academy.evaluation'].create({
            'name': 'First',
            'sequence': 1,
        })
        self.evaluation_02 = self.env['academy.evaluation'].create({
            'name': 'Second',
            'sequence': 2,
        })
        self.evaluation_03 = self.env['academy.evaluation'].create({
            'name': 'Third',
            'sequence': 2,
        })
        self.mark_01 = self.env['academy.evaluable.concept.mark'].create({
            'name': 'Mark 01',
        })
        self.mark_02 = self.env['academy.evaluable.concept.mark'].create({
            'name': 'Mark 02',
        })
        self.concept_01 = self.env['academy.evaluable.concept'].create({
            'name': 'Concept_01',
            'eval_concept_mark_ids': [
                Command.set([self.mark_01.id, self.mark_02.id])],
        })
        self.concept_02 = self.env['academy.evaluable.concept'].create({
            'name': 'Concept_02',
            'eval_concept_mark_ids': [
                Command.set([self.mark_01.id, self.mark_02.id])],
        })
        self.activity_01 = self.env['academy.activity'].create({
            'name': 'Activity 01',
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=31, month=12),
            'training_plan_id': self.training_plan_01.id,
            'teacher_id': self.teacher_01.id,
            'user_id': self.manager_01.id,
            'evaluation_ids': [Command.set(self.evaluation_01.ids)],
            'evaluable_concept_ids': [Command.set(self.concept_01.ids)],
        })
        self.activity_02 = self.env['academy.activity'].create({
            'name': 'Activity 02',
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=31, month=12),
            'user_id': self.manager_01.id,
            'training_plan_id': self.training_plan_02.id,
            'teacher_id': self.teacher_01.id,
            'evaluation_ids': [Command.set(self.evaluation_01.ids)],
            'evaluable_concept_ids': [Command.set(self.concept_01.ids)],
        })
        self.activity_03 = self.env['academy.activity'].create({
            'name': 'Activity 03',
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=31, month=12),
            'user_id': self.manager_01.id,
            'training_plan_id': self.training_plan_01.id,
            'evaluation_ids': [Command.set(self.evaluation_01.ids)],
            'teacher_id': self.teacher_01.id,
            'evaluable_concept_ids': [Command.set(self.concept_01.ids)],
        })
