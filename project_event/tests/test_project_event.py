###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectEvent(TransactionCase):

    def date2str(self, date):
        return date.strftime('%Y/%m/%d %H:%M')

    def test_project_event_generator(self):
        project = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'date_begin': '2022/01/01',
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
            '2022/12/01 00:00')
        self.assertEquals(
            project.event_line_ids[0].event_ids, project.event_ids)

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
                    'repeat': 5,
                    'period': 'week',
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
        product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Service test',
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
                }),
            ],
        })
        project.product_line_ids[0].onchange_product_id()
        self.assertEquals(product.name, project.product_line_ids[0].name)
        project.project_status = status.id
        self.assertEquals(len(project.event_ids), 5)
        self.assertEquals(len(project.event_ids[0].product_ids), 1)
        event = project.event_ids[0]
        event.button_confirm()
        self.assertTrue(event.product_ids.task_id)
