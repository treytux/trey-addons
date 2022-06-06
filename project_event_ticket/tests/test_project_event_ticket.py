###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectEvent(TransactionCase):

    def date2str(self, date):
        return date.strftime('%Y/%m/%d %H:%M')

    def test_project_event_generator(self):
        product_ticket = self.env.ref(
            'event_sale.product_product_event')
        project = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'date_begin': '2022/01/01',
                    'repeat': 12,
                    'period': 'month',
                }),
            ],
            'event_ticket_ids': [
                (0, 0, {
                    'name': 'Test ticket',
                    'deadline': '2022/01/01',
                    'price': 12,
                    'seats_max': 50,
                    'product_id': product_ticket.id,
                }),
            ],
        })
        project.generate_events()
        self.assertEquals(len(project.event_ids), 12)
        self.assertEquals(project.event_count, 12)
        self.assertEquals(len(project.event_ids.mapped('event_ticket_ids')), 12)
        self.assertEquals(
            self.date2str(project.event_ids[-1].date_begin),
            '2022/12/01 00:00')
        event_ticket = project.event_ids[-1].event_ticket_ids[0]
        self.assertEquals(
            self.date2str(event_ticket.deadline), '2022/01/01 00:00')
        self.assertEquals(event_ticket.name, 'Test ticket')
        self.assertEquals(event_ticket.price, 12)
        self.assertEquals(event_ticket.seats_max, 50)
        self.assertEquals(event_ticket.product_id, product_ticket)
        self.assertEquals(
            project.event_line_ids[0].event_ids, project.event_ids)
