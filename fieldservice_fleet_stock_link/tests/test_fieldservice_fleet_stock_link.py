###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestFieldserviceFleetStockLink(TransactionCase):

    def setUp(self):
        super().setUp()
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.partner = self.env['res.partner'].create({
            'name': 'Test customer',
            'customer': True,
        })
        self.partner_driver_fsm = self.env['res.partner'].create({
            'name': 'Test fsm driver worker',
            'customer': True,
        })
        self.env['fsm.wizard'].action_convert_person(self.partner_driver_fsm)
        self.assertTrue(self.partner_driver_fsm.fsm_person)
        self.partner_fsm = self.env['res.partner'].create({
            'name': 'Test fsm worker',
            'customer': True,
        })
        self.env['fsm.wizard'].action_convert_person(self.partner_fsm)
        self.assertTrue(self.partner_fsm.fsm_person)
        self.partner_multi_driver_fsm = self.env['res.partner'].create({
            'name': 'Test fsm multi driver worker',
            'customer': True,
        })
        self.env['fsm.wizard'].action_convert_person(
            self.partner_multi_driver_fsm)
        self.assertTrue(self.partner_multi_driver_fsm.fsm_person)
        self.fsm_location = self.env['fsm.location'].create({
            'name': 'Test location2',
            'owner_id': self.partner.id,
        })
        self.vehicle = self.env['fleet.vehicle'].create({
            'license_plate': 'Test vehicle',
            'model_id': self.env.ref('fleet.model_astra').id,
            'driver_id': self.partner_driver_fsm.id,
        })
        self.vehicle2 = self.env['fleet.vehicle'].create({
            'license_plate': 'Test vehicle 2',
            'model_id': self.env.ref('fleet.model_astra').id,
            'driver_id': self.partner_multi_driver_fsm.id,
        })
        self.vehicle3 = self.env['fleet.vehicle'].create({
            'license_plate': 'Test vehicle 3',
            'model_id': self.env.ref('fleet.model_astra').id,
            'driver_id': self.partner_multi_driver_fsm.id,
        })
        self.stock_wh_vehicle = self.env['stock.warehouse'].create({
            'name': 'Test vehicle wh',
            'code': 'TESTV',
            'vehicle_id': self.vehicle.id,
        })
        self.stock_wh_vehicle2 = self.env['stock.warehouse'].create({
            'name': 'Test vehicle wh 2',
            'code': 'TSTV2',
            'vehicle_id': self.vehicle2.id,
        })

    def test_assign_driver_worker(self):
        fsm_driver_worker = self.env['fsm.person'].search([
            ('name', '=', 'Test fsm driver worker'),
        ])
        fsm_order = self.env['fsm.order'].new({
            'name': 'Test fms order',
            'location_id': self.fsm_location.id,
        })
        self.assertFalse(fsm_order.person_id)
        fsm_order.update({
            'person_id': fsm_driver_worker.id,
            'vehicle_id': self.vehicle.id,
        })
        fsm_order._onchange_warehouse_relations()
        fsm_order = self.env['fsm.order'].create(fsm_order._convert_to_write(
            fsm_order._cache))
        self.assertEquals(fsm_order.warehouse_id, self.stock_wh_vehicle)

    def test_assign_no_driver_worker(self):
        fsm_person = self.env['fsm.person'].search([
            ('name', '=', 'Test fsm worker'),
        ])
        fsm_order = self.env['fsm.order'].create({
            'name': 'Test fms order',
            'location_id': self.fsm_location.id,
        })
        self.assertFalse(fsm_order.person_id)
        with self.assertRaises(exceptions.ValidationError) as result:
            fsm_order.write({
                'vehicle_id': self.vehicle.id,
                'person_id': fsm_person.id,
            })
        self.assertEqual(
            result.exception.name,
            'Vehicle Opel/Astra/Test vehicle is not assigned to driver Test fsm '
            'worker')

    def test_assign_multi_driver_worker(self):
        fsm_multi_driver_worker = self.env['fsm.person'].search([
            ('name', '=', 'Test fsm multi driver worker')])
        fsm_order = self.env['fsm.order'].new({
            'name': 'Test fms order',
            'location_id': self.fsm_location.id,
        })
        self.assertFalse(fsm_order.person_id)
        fsm_order.update({
            'person_id': fsm_multi_driver_worker.id,
            'vehicle_id': self.vehicle2.id,
            'warehouse_id': self.stock_wh_vehicle2.id,
        })
        fsm_order._onchange_warehouse_relations()
        fsm_order = self.env['fsm.order'].create(fsm_order._convert_to_write(
            fsm_order._cache))

    def test_assign_driver_worker_with_anoter_wh(self):
        fsm_order = self.env['fsm.order'].new({
            'name': 'Test fms order',
            'location_id': self.fsm_location.id,
        })
        fsm_driver_worker = self.env['fsm.person'].search([
            ('name', '=', 'Test fsm driver worker')])
        self.assertFalse(fsm_order.person_id)
        fsm_order.update({
            'person_id': fsm_driver_worker.id,
            'vehicle_id': self.vehicle.id,
        })
        fsm_order._onchange_warehouse_relations()
        fsm_order = self.env['fsm.order'].create(fsm_order._convert_to_write(
            fsm_order._cache))
        with self.assertRaises(exceptions.ValidationError) as result:
            fsm_order.warehouse_id = self.stock_wh.id
        self.assertEqual(
            result.exception.name,
            'Warehouse YourCompany is not assigned to one of worker vehicles')

    def test_assign_warehouse_without_vehicle_assigned(self):
        fsm_order = self.env['fsm.order'].new({
            'name': 'Test fms order',
            'location_id': self.fsm_location.id,
        })
        fsm_driver_worker = self.env['fsm.person'].search([
            ('name', '=', 'Test fsm driver worker')])
        self.assertFalse(fsm_order.person_id)
        fsm_order.update({
            'person_id': fsm_driver_worker.id,
            'vehicle_id': self.vehicle.id,
        })
        fsm_order._onchange_warehouse_relations()
        fsm_order = self.env['fsm.order'].create(fsm_order._convert_to_write(
            fsm_order._cache))
        with self.assertRaises(exceptions.ValidationError) as result:
            fsm_order.write({
                'warehouse_id': self.stock_wh_vehicle.id,
                'vehicle_id': False,
            })
        self.assertEqual(
            result.exception.name,
            'Vehicle False is not assigned to driver Test fsm driver worker')

    def test_assign_warehouse_without_vehicle(self):
        fsm_order = self.env['fsm.order'].new({
            'name': 'Test fms order',
            'location_id': self.fsm_location.id,
        })
        fsm_driver_worker = self.env['fsm.person'].search([
            ('name', '=', 'Test fsm driver worker')])
        self.assertFalse(fsm_order.person_id)
        fsm_order.person_id = fsm_driver_worker.id
        fsm_order.update({
            'person_id': fsm_driver_worker.id,
            'warehouse_id': self.stock_wh_vehicle.id,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            fsm_order = self.env['fsm.order'].create(fsm_order._convert_to_write(
                fsm_order._cache))
        self.assertEqual(
            result.exception.name,
            'Vehicle False is not assigned to driver Test fsm driver worker')
