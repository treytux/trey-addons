###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestEventMultipleAddresses(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.partner_main_location = self.env['res.partner'].create({
            'name': 'Main location',
        })
        self.partner_location1 = self.env['res.partner'].create({
            'name': 'Location1',
        })
        self.partner_location2 = self.env['res.partner'].create({
            'name': 'Location2',
        })
        self.event = self.env['event.event'].create({
            'name': 'Test event',
            'date_begin': '2022-12-05 00:00:00',
            'date_end': '2022-12-05 23:59:00',
            'address_id': self.partner_main_location.id,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'name': 'Product',
        })

    def test_compute_addresses(self):
        self.assertEqual(self.event.addresses, 'Main location')
        self.event.address_ids = [(4, self.partner_location1.id)]
        self.assertEqual(self.event.addresses, 'Main location, Location1')
        self.event.address_ids = [(4, self.partner_location2.id)]
        self.assertEqual(
            self.event.addresses, 'Main location, Location1, Location2')
        self.event.address_id = False
        self.assertEqual(self.event.addresses, 'Location1, Location2')
        self.event.address_ids = False
        self.assertEqual(self.event.addresses, '')

    def test_constraint_product_event_location(self):
        self.event.product_ids = [(0, 0, {
            'name': self.product.name,
            'product_id': self.product.id,
            'address_id': self.partner_main_location.id
        })]
        self.assertEqual(self.event.addresses, 'Main location')
        self.event.address_ids = [(4, self.partner_location1.id)]
        self.event.product_ids = [(0, 0, {
            'name': self.product.name,
            'product_id': self.product.id,
            'address_id': self.partner_location1.id
        })]
        self.assertEqual(self.event.addresses, 'Main location, Location1')
        self.event.address_ids = [(4, self.partner_location2.id)]
        self.event.product_ids = [(0, 0, {
            'name': self.product.name,
            'product_id': self.product.id,
            'address_id': self.partner_location2.id
        })]
        self.assertEqual(
            self.event.addresses, 'Main location, Location1, Location2')
        self.event.address_id = False
        self.assertEqual(self.event.addresses, 'Location1, Location2')
        with self.assertRaises(ValidationError) as result:
            self.event.address_ids = False
        self.assertEqual(
            result.exception.name,
            '\'%s\' location of product \'%s\' not in event addresses.'
            % (self.partner_main_location.name, self.product.name))
        self.assertEqual(self.event.addresses, '')

    def test_event_overlap_addresses(self):
        project = self.env['project.project'].create({
            'name': 'Project test',
        })
        project_event_line_1_error = self.env['project.event.line'].create({
            'project_id': project.id,
            'address_id': self.partner_main_location.id,
            'date_begin': '2022-12-05 00:00:00',
            'date_end': '2022-12-05 23:59:00',
        })
        with self.assertRaises(ValidationError) as result:
            project_event_line_1_error.generate_events()
        self.assertEqual(
            result.exception.name,
            'Location(s) already taken in another event.')
        self.event.address_ids = [(4, self.partner_location1.id)]
        project_event_line_2_error = self.env['project.event.line'].create({
            'project_id': project.id,
            'address_id': self.partner_main_location.id,
            'address_ids': [(4, self.partner_location1.id)],
            'date_begin': '2022-12-05 00:00:00',
            'date_end': '2022-12-05 23:59:00',
        })
        with self.assertRaises(ValidationError) as result:
            project_event_line_2_error.generate_events()
        self.assertEqual(
            result.exception.name,
            'Location(s) already taken in another event.')
        project_event_line_ok = self.env['project.event.line'].create({
            'project_id': project.id,
            'address_id': self.partner_main_location.id,
            'address_ids': [(4, self.partner_location1.id)],
            'date_begin': '2022-12-06 00:00:00',
            'date_end': '2022-12-06 23:59:00',
        })
        self.assertFalse(project_event_line_ok.event_ids)
        project_event_line_ok.generate_events()
        self.assertEqual(len(project_event_line_ok.event_ids), 1)
