###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestProjectEvent(TransactionCase):

    def date2str(self, date):
        return date.strftime('%Y/%m/%d %H:%M')

    def test_project_event_generator(self):
        project = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'date_begin': '2022/01/01 13:00:00',
                    'date_end': '2022/01/01 13:30:00',
                    'repeat': 12,
                    'period': 'month',
                }),
            ],
        })
        project.generate_events()
        self.assertEquals(len(project.event_ids), 12)
        self.assertEquals(project.event_count, 12)
        self.assertEquals(
            self.date2str(project.event_ids[-1].date_begin),
            '2022/12/01 13:00')
        self.assertEquals(
            project.event_line_ids[0].event_ids, project.event_ids)

    def test_project_event_generator_weekly(self):
        project_01 = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'date_begin': '2024/02/05 00:00:00',
                    'date_end': '2024/02/05 18:00:00',
                    'period': 'week',
                    'days_repeat': [(6, 0, [
                        self.env.ref('project_event.event_day_monday').id,
                    ])],
                    'date_end_repeat': '2024/02/26',
                }),
            ],
        })
        project_01.generate_events()
        self.assertEquals(project_01.event_count, 4)
        event_1 = project_01.event_ids[0]
        self.assertEquals(
            self.date2str(event_1.date_begin), '2024/02/05 00:00')
        self.assertEquals(
            self.date2str(event_1.date_end), '2024/02/05 18:00')
        event_2 = project_01.event_ids[1]
        self.assertEquals(
            self.date2str(event_2.date_begin), '2024/02/12 00:00')
        self.assertEquals(
            self.date2str(event_2.date_end), '2024/02/12 18:00')
        event_3 = project_01.event_ids[2]
        self.assertEquals(
            self.date2str(event_3.date_begin), '2024/02/19 00:00')
        self.assertEquals(
            self.date2str(event_3.date_end), '2024/02/19 18:00')
        event_4 = project_01.event_ids[3]
        self.assertEquals(
            self.date2str(event_4.date_begin), '2024/02/26 00:00')
        self.assertEquals(
            self.date2str(event_4.date_end), '2024/02/26 18:00')
        project_02 = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'date_begin': '2024/02/05 00:00:00',
                    'date_end': '2024/02/05 18:00:00',
                    'period': 'week',
                    'days_repeat': [(6, 0, [
                        self.env.ref('project_event.event_day_tuesday').id,
                    ])],
                    'date_end_repeat': '2024/02/26',
                }),
            ],
        })
        project_02.generate_events()
        self.assertEquals(project_02.event_count, 3)
        event_1 = project_02.event_ids[0]
        self.assertEquals(
            self.date2str(event_1.date_begin), '2024/02/06 00:00')
        self.assertEquals(
            self.date2str(event_1.date_end), '2024/02/06 18:00')
        event_2 = project_02.event_ids[1]
        self.assertEquals(
            self.date2str(event_2.date_begin), '2024/02/13 00:00')
        self.assertEquals(
            self.date2str(event_2.date_end), '2024/02/13 18:00')
        event_3 = project_02.event_ids[2]
        self.assertEquals(
            self.date2str(event_3.date_begin), '2024/02/20 00:00')
        self.assertEquals(
            self.date2str(event_3.date_end), '2024/02/20 18:00')
        project_03 = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'date_begin': '2024/02/06 00:00:00',
                    'date_end': '2024/02/06 18:00:00',
                    'period': 'week',
                    'days_repeat': [(6, 0, [
                        self.env.ref('project_event.event_day_monday').id,
                    ])],
                    'date_end_repeat': '2024/02/25',
                }),
            ],
        })
        project_03.generate_events()
        self.assertEquals(project_03.event_count, 2)
        event_1 = project_03.event_ids[0]
        self.assertEquals(
            self.date2str(event_1.date_begin), '2024/02/12 00:00')
        self.assertEquals(
            self.date2str(event_1.date_end), '2024/02/12 18:00')
        event_2 = project_03.event_ids[1]
        self.assertEquals(
            self.date2str(event_2.date_begin), '2024/02/19 00:00')
        self.assertEquals(
            self.date2str(event_2.date_end), '2024/02/19 18:00')

    def test_project_event_generator_with_change_tz_offset(self):
        project_tz = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'date_begin': '2024/03/25 00:00:00',
                    'date_end': '2024/03/25 18:00:00',
                    'period': 'week',
                    'days_repeat': [(6, 0, [
                        self.env.ref('project_event.event_day_monday').id,
                    ])],
                    'date_end_repeat': '2024/04/01',
                }),
            ],
        })
        project_tz.generate_events()
        self.assertEquals(project_tz.event_count, 2)
        event_1 = project_tz.event_ids[0]
        self.assertEquals(
            self.date2str(event_1.date_begin), '2024/03/25 00:00')
        self.assertEquals(
            self.date2str(event_1.date_end), '2024/03/25 18:00')
        event_2 = project_tz.event_ids[1]
        self.assertEquals(
            self.date2str(event_2.date_begin), '2024/03/31 23:00')
        self.assertEquals(
            self.date2str(event_2.date_end), '2024/04/01 17:00')

    def test_project_event_generator_weekly_error_same_day(self):
        project_to_next_day = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'date_begin': '2024/02/05 23:00:00',
                    'date_end': '2024/02/06 00:00:00',
                    'period': 'week',
                    'days_repeat': [(6, 0, [
                        self.env.ref('project_event.event_day_monday').id,
                    ])],
                    'date_end_repeat': '2024/02/26',
                }),
            ],
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            project_to_next_day.generate_events()
        self.assertIn(
            'start and end date must be in same day', result.exception.name)

    def test_project_event_end(self):
        project = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'date_begin': '2022/01/01 12:30:00',
                    'date_end': '2022/01/01 13:30:00',
                    'repeat': 5,
                    'period': 'day',
                }),
            ],
        })
        project.generate_events()
        self.assertEquals(project.event_count, 5)
        event = project.event_ids[-1]
        self.assertEquals(self.date2str(event.date_begin), '2022/01/05 12:30')
        self.assertEquals(self.date2str(event.date_end), '2022/01/05 13:30')
        project = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'date_begin': '2022/01/01 12:30:00',
                    'date_end': '2022/01/01 13:30:00',
                    'period': 'week',
                    'days_repeat': [(6, 0, [
                        self.env.ref('project_event.event_day_saturday').id,
                    ])],
                    'date_end_repeat': '2022/01/29',
                }),
            ],
        })
        project.generate_events()
        self.assertEquals(project.event_count, 5)
        event = project.event_ids[-1]
        self.assertEquals(self.date2str(event.date_begin), '2022/01/29 12:30')
        self.assertEquals(self.date2str(event.date_end), '2022/01/29 13:30')

    def test_project_event_partner(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        project = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'address_id': partner.id,
                    'date_begin': '2022/01/01 12:30:00',
                    'date_end': '2022/01/01 13:30:00',
                    'repeat': 5,
                    'period': 'day',
                }),
            ],
        })
        project.generate_events()
        self.assertEquals(project.event_ids[0].address_id, partner)

    def test_project_product(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_no_one').id,
            ])],
        })
        product_service = self.env['product.product'].create({
            'type': 'service',
            'name': 'Service test',
            'standard_price': 10,
            'list_price': 100,
            'service_tracking': 'task_new_project',
        })
        product = self.env['product.product'].create({
            'type': 'consu',
            'name': 'Consumable test',
            'standard_price': 10,
            'list_price': 100,
            'service_tracking': 'task_new_project',
        })
        status = self.env['project.status'].create({
            'name': 'Generate events',
            'not_modify_event': True,
        })
        project = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'address_id': partner.id,
                    'date_begin': '2022/01/01 12:30:00',
                    'date_end': '2022/01/01 13:30:00',
                    'repeat': 5,
                    'period': 'day',
                }),
            ],
            'product_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'quantity': 10,
                    'user_id': user.id,
                }),
            ],
            'service_line_ids': [
                (0, 0, {
                    'product_id': product_service.id,
                    'quantity': 10,
                    'user_id': user.id,
                }),
            ],
        })
        project.product_line_ids[0].onchange_product_id()
        self.assertEquals(product.name, project.product_line_ids[0].name)
        project.service_line_ids[0].onchange_product_id()
        self.assertEquals(
            product_service.name, project.service_line_ids[0].name)
        project.project_status = status.id
        self.assertEquals(len(project.event_ids), 5)
        self.assertEquals(len(project.event_ids[0].product_line_ids), 1)
        event = project.event_ids[0]
        event.create_services_and_material()
        event.button_confirm()
        self.assertTrue(event.service_line_ids.task_id)
        task = event.service_line_ids.task_id
        self.assertEquals(task.user_id, user)
        self.assertEquals(self.date2str(task.date_deadline), '2022/01/01 12:30')
        self.assertEquals(task.planned_hours, 1)

    def test_wizard_event_create_services_materials(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_no_one').id,
            ])],
        })
        product_service = self.env['product.product'].create({
            'type': 'service',
            'name': 'Service test',
            'standard_price': 10,
            'list_price': 100,
            'service_tracking': 'task_new_project',
        })
        product = self.env['product.product'].create({
            'type': 'consu',
            'name': 'Consumable test',
            'standard_price': 10,
            'list_price': 100,
            'service_tracking': 'task_new_project',
        })
        status = self.env['project.status'].create({
            'name': 'Generate events',
            'not_modify_event': True,
        })
        project = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'address_id': partner.id,
                    'date_begin': '2022/01/01 12:30:00',
                    'date_end': '2022/01/01 13:30:00',
                    'repeat': 5,
                    'period': 'day',
                }),
            ],
            'product_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'quantity': 10,
                    'user_id': user.id,
                }),
            ],
            'service_line_ids': [
                (0, 0, {
                    'product_id': product_service.id,
                    'quantity': 10,
                    'user_id': user.id,
                }),
            ],
        })
        project.product_line_ids[0].onchange_product_id()
        self.assertEquals(product.name, project.product_line_ids[0].name)
        project.service_line_ids[0].onchange_product_id()
        self.assertEquals(
            product_service.name, project.service_line_ids[0].name)
        project.project_status = status.id
        self.assertEquals(len(project.event_ids), 5)
        self.assertEquals(len(project.event_ids[0].product_line_ids), 1)
        event = project.event_ids[0]
        wiz = self.env['wizard.event.create.services.materials'].with_context(
            active_model='event.event',
            active_ids=[event.id],
        ).create({})
        self.assertEquals(len(wiz.line_ids), 1)
        self.assertEquals(wiz.line_ids.product_id, product_service)
        self.assertEquals(wiz.line_ids.generate, True)
        self.assertEquals(wiz.button_confirm(), True)
        wiz.button_confirm()
        self.assertTrue(event.service_line_ids.task_id)
        task = event.service_line_ids.task_id
        self.assertEquals(task.user_id, user)
        self.assertEquals(self.date2str(task.date_deadline), '2022/01/01 12:30')
        self.assertEquals(task.planned_hours, 1)
