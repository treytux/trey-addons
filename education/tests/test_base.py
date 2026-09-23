###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestBase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.state_01 = self.env.ref('base.state_es_gr')
        self.teacher_01 = self.env['res.partner'].create({
            'name': 'Teacher 01',
            'supplier': True,
            'is_teacher': True,
            'customer': False,
            'email': 'teacher_01@test.com',
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
        self.teacher_02 = self.env['res.partner'].create({
            'name': 'Teacher 02',
            'supplier': True,
            'is_teacher': True,
            'customer': False,
            'email': 'teacher_02@test.com',
            'street': 'Street, 2',
            'street2': 'Street2, 2',
            'city': 'City 2',
            'zip': '18001',
            'state_id': self.state_01.id,
            'country_id': self.env['res.country'].search([
                ('code', '=', 'ES'),
            ]).id,
            'phone': '958010203',
        })
        self.mother_01 = self.env['res.partner'].create({
            'name': 'Mother 01',
            'customer': True,
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
            'customer': True,
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
        self.student_01 = self.env['res.partner'].create({
            'name': 'Student 01',
            'customer': True,
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
            'customer': True,
            'tutor_ids': [(6, 0, self.father_01.ids)],
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
        self.subject_01 = self.env['edu.subject'].create({
            'name': 'Subject 01',
            'short_name': 'S01',
            'evaluable_concept_ids': [(0, 0, {
                'name': 'Concept 01',
                'value_type': 'text',
                'values_valid': 'PA,PB,PC,PD',
            })]
        })
        self.subject_02 = self.env['edu.subject'].create({
            'name': 'Subject 02',
            'short_name': 'S02',
        })
        self.subject_03 = self.env['edu.subject'].create({
            'name': 'Subject 03',
            'short_name': 'S03',
        })
        self.training_plan_01 = self.env['edu.training.plan'].create({
            'name': 'Trainig Plan 01',
            'short_name': 'TP01',
            'start_date': '2016-09-15',
            'end_date': '2017-07-01',
            'description': '''
            Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean
            commodo ligula eget dolor. Aenean massa. Cum sociis natoque
            penatibus et magnis dis parturient montes, nascetur ridiculus mus.
            Donec quam felis, ultricies nec, pellentesque eu, pretium quis,
            sem.
            ''',
        })
        self.training_plan_02 = self.env['edu.training.plan'].create({
            'name': 'Trainig Plan 02',
            'short_name': 'TP02',
            'start_date': '2016-10-01',
            'end_date': '2017-06-01',
            'description': '''
            Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean
            commodo ligula eget dolor. Aenean massa. Cum sociis natoque
            penatibus et magnis dis parturient montes, nascetur ridiculus mus.
            Donec quam felis, ultricies nec, pellentesque eu, pretium quis,
            sem.
            ''',
        })
        self.classroom_01 = self.env['edu.training.plan.classroom'].create({
            'training_plan_id': self.training_plan_01.id,
            'course': '1º',
            'group': 'A',
        })
        self.classroom_02 = self.env['edu.training.plan.classroom'].create({
            'training_plan_id': self.training_plan_02.id,
            'course': '1º',
            'group': 'B',
        })
        self.training_plan_line_01 = self.env['edu.training.plan.line'].create({
            'start_date': '2016-09-15',
            'end_date': '2017-07-01',
            'training_plan_id': self.training_plan_01.id,
            'subject_id': self.subject_01.id,
            'teacher_id': self.teacher_01.id,
            'classroom_id': self.classroom_01.id,
        })
        self.training_plan_line_02 = self.env['edu.training.plan.line'].create({
            'start_date': '2016-09-15',
            'end_date': '2017-07-01',
            'training_plan_id': self.training_plan_02.id,
            'subject_id': self.subject_02.id,
            'teacher_id': self.teacher_01.id,
            'classroom_id': self.classroom_02.id,
        })
        self.training_plan_line_03 = self.env['edu.training.plan.line'].create({
            'start_date': '2016-09-15',
            'end_date': '2017-07-01',
            'training_plan_id': self.training_plan_01.id,
            'subject_id': self.subject_03.id,
            'teacher_id': self.teacher_01.id,
            'classroom_id': self.classroom_01.id,
        })
        self.evaluation_01 = self.env['edu.evaluation'].create({
            'name': 'First',
            'sequence': 1,
        })
        self.evaluation_02 = self.env['edu.evaluation'].create({
            'name': 'Second',
            'sequence': 2,
        })
