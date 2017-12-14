# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common


class TestBase(common.TransactionCase):

    def setUp(self):
        super(TestBase, self).setUp()
        self.state_01 = self.env['res.country.state'].create({
            'name': 'Graná',
            'code': 'GR',
            'country_id': self.env['res.country'].search(
                [('code', '=', 'ES')]).id})
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
            'country_id': self.env['res.country'].search(
                [('code', '=', 'ES')]).id,
            'phone': '958010203',
            'vat': '12345678A'})
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
            'country_id': self.env['res.country'].search(
                [('code', '=', 'ES')]).id,
            'phone': '958010203',
            'vat': '12345678A'})
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
            'country_id': self.env['res.country'].search(
                [('code', '=', 'ES')]).id,
            'phone': '958010203',
            'vat': '12345678A'})
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
            'country_id': self.env['res.country'].search(
                [('code', '=', 'ES')]).id,
            'phone': '958010203',
            'vat': '12345678A'})
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
            'country_id': self.env['res.country'].search(
                [('code', '=', 'ES')]).id,
            'phone': '958010203',
            'vat': '12345678A'})
        self.subject_01 = self.env['edu.subject'].create({
            'name': 'Subject 01',
            'short_name': 'S01'})
        self.subject_02 = self.env['edu.subject'].create({
            'name': 'Subject 02',
            'short_name': 'S02'})
        self.subject_03 = self.env['edu.subject'].create({
            'name': 'Subject 03',
            'short_name': 'S03'})
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
            sem. Nulla consequat massa quis enim. Donec pede justo, fringilla
            vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut,
            imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede
            mollis pretium. Integer tincidunt. Cras dapibus. Vivamus elementum
            semper nisi. Aenean vulputate eleifend tellus. Aenean leo ligula,
            porttitor eu, consequat vitae, eleifend ac, enim. Aliquam lorem
            ante, dapibus in, viverra quis, feugiat a, tellus. Phasellus
            viverra nulla ut metus varius laoreet. Quisque rutrum. Aenean
            imperdiet. Etiam ultricies nisi vel augue. Curabitur ullamcorper
            ultricies nisi. Nam eget dui. Etiam rhoncus. Maecenas tempus,
            tellus eget condimentum rhoncus, sem quam semper libero, sit amet
            adipiscing sem neque sed ipsum. Nam quam nunc, blandit vel, luctus
            pulvinar, hendrerit id, lorem. Maecenas nec odio et ante tincidunt
            tempus. Donec vitae sapien ut libero venenatis faucibus. Nullam
            quis ante. Etiam sit amet orci eget eros faucibus tincidunt. Duis
            leo. Sed fringilla mauris sit amet nibh. Donec sodales sagittis
            magna. Sed consequat, leo eget bibendum sodales, augue velit cursus
            nunc
            '''})
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
            sem. Nulla consequat massa quis enim. Donec pede justo, fringilla
            vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut,
            imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede
            mollis pretium. Integer tincidunt. Cras dapibus. Vivamus elementum
            semper nisi. Aenean vulputate eleifend tellus. Aenean leo ligula,
            porttitor eu, consequat vitae, eleifend ac, enim. Aliquam lorem
            ante, dapibus in, viverra quis, feugiat a, tellus. Phasellus
            viverra nulla ut metus varius laoreet. Quisque rutrum. Aenean
            imperdiet. Etiam ultricies nisi vel augue. Curabitur ullamcorper
            ultricies nisi. Nam eget dui. Etiam rhoncus. Maecenas tempus,
            tellus eget condimentum rhoncus, sem quam semper libero, sit amet
            adipiscing sem neque sed ipsum. Nam quam nunc, blandit vel, luctus
            pulvinar, hendrerit id, lorem. Maecenas nec odio et ante tincidunt
            tempus. Donec vitae sapien ut libero venenatis faucibus. Nullam
            quis ante. Etiam sit amet orci eget eros faucibus tincidunt. Duis
            leo. Sed fringilla mauris sit amet nibh. Donec sodales sagittis
            magna. Sed consequat, leo eget bibendum sodales, augue velit cursus
            nunc
            '''})
        self.classroom_01 = self.env['edu.training.plan.classroom'].create({
            'training_plan_id': self.training_plan_01.id,
            'course': '1º',
            'group': 'A'})
        self.classroom_02 = self.env['edu.training.plan.classroom'].create({
            'training_plan_id': self.training_plan_01.id,
            'course': '1º',
            'group': 'B'})
        self.training_plan_line_01 = self.env['edu.training.plan.line'].create(
            {'training_plan_id': self.training_plan_01.id,
             'subject_id': self.subject_01.id,
             'teacher_id': self.teacher_01.id,
             'classroom_id': self.classroom_01.id})
        self.training_plan_line_02 = self.env['edu.training.plan.line'].create(
            {'training_plan_id': self.training_plan_01.id,
             'subject_id': self.subject_02.id,
             'teacher_id': self.teacher_01.id,
             'classroom_id': self.classroom_01.id})
        self.training_plan_line_03 = self.env['edu.training.plan.line'].create(
            {'training_plan_id': self.training_plan_01.id,
             'subject_id': self.subject_03.id,
             'teacher_id': self.teacher_01.id,
             'classroom_id': self.classroom_01.id})
