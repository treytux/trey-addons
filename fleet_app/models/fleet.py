# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields, exceptions, _
import logging
_log = logging.getLogger(__name__)


class FleetApp(models.AbstractModel):
    _name = 'fleet.app'
    _description = 'Fleet App'

    @api.model
    def get_vehicles(self, driver_id=None):
        driver_id = driver_id or self.env.user.partner_id.id
        vehicles = self.env['fleet.vehicle'].search(
            [('driver_id', '=', driver_id)])
        return [{
            'id': v.id,
            'license_plate': v.license_plate,
            'model': v.model_id.name
            } for v in vehicles]

    @api.model
    def get_current_vehicle(self, user_id=None):
        user = user_id and self.env.user.browse(user_id) or self.env.user
        vehicle = user.current_vehicle_id
        if not vehicle:
            return False
        return {
            'id': vehicle.id,
            'model_name': vehicle.model_id.name,
            'license_plate': vehicle.license_plate,
            'stock_location_id': vehicle.stock_location_id.id}

    @api.model
    def set_fuel_log(self, odometer, liter, amount, inv_ref=None,
                     notes=None, driver_id=None):
        driver_id = driver_id or self.env.user.partner_id.id
        vehicles = self.env['fleet.vehicle'].sudo().search(
            [('driver_id', '=', driver_id)], limit=1)

        if not vehicles:
            return False

        def parse_float(value):
            try:
                value = str(value).replace(',', '.')
                return value and float(value) or 0.0
            except:
                return 0.0

        log = self.env['fleet.vehicle.log.fuel'].sudo().create({
            'vehicle_id': vehicles[0].id,
            'liter': liter,
            'odometer': odometer,
            'amount': amount,
            'price_per_liter': round(
                parse_float(amount) / parse_float(liter), 2),
            'inv_ref': inv_ref,
            'notes': notes})
        return log.id and True or False

    @api.model
    def get_fuel_logs(self, vehicle_id=None):

        def compare_date(a, b):
            aa = fields.Date.from_string(a['date'])
            bb = fields.Date.from_string(b['date'])
            return (aa == bb) and 0 or ((aa < bb) and 1 or -1)

        fuel_logs = {}

        if not vehicle_id:
            # TODO: Asignar permisos a comerciales y quitar sudo()
            # TODO: El vehículo actual se obtendrá de un campo default_vehicle
            # del partner asociado al usuario que está pendiente de agregar
            vehicles = self.env['fleet.vehicle'].sudo().search(
                [('driver_id', '=', self.env.user.partner_id.id)])
            if vehicles:
                vehicle_id = vehicles[0].id

        if vehicle_id:
            # TODO: Asignar permisos a comerciales y quitar sudo()
            vehicle = self.env['fleet.vehicle'].sudo().browse(vehicle_id)
            if vehicle:
                fuel_logs = {
                    'id': vehicle.id,
                    'brand': vehicle.model_id.brand_id.name,
                    'model': vehicle.model_id.modelname,
                    'license_plate': vehicle.license_plate,
                    'driver': (
                        vehicle.driver_id and vehicle.driver_id.name or ''),
                    'driver_id': (
                        vehicle.driver_id and vehicle.driver_id.id or -1),
                    'logs': []
                }
                if vehicle.log_fuel:
                    fuel_logs.update({'logs': sorted([{
                        'liter': lf.liter,
                        'price_per_liter': lf.price_per_liter,
                        'amount': lf.amount,
                        'odometer': lf.odometer,
                        'date': lf.date
                    } for lf in vehicle.log_fuel], cmp=compare_date)})

        return fuel_logs

    @api.model
    def inventory_ajust(self, vehicle_id, lines):
        vehicle = self.env['fleet.vehicle'].browse(vehicle_id)
        if not vehicle.stock_location_id:
            raise exceptions.Warning(
                _('El vehiculo "" no tiene asignada una ubicacion de '
                  'stock') % (vehicle.name))
        inventory = self.env['stock.inventory'].create({
            'name': '[%s] %s: Regularizacion previa a carga' % (
                vehicle.name, self.env.user.name),
            'company_id': self.env.user.company_id.id,
            'location_id': vehicle.stock_location_id.id,
            'filter': 'partial'})
        inventory.prepare_inventory()
        for product_id, qty in lines.iteritems():
            product = self.env['product.product'].browse(int(product_id))
            self.env['stock.inventory.line'].create({
                'inventory_id': inventory.id,
                'product_id': product_id,
                'product_uom_id': product.uom_id.id,
                'location_id': vehicle.stock_location_id.id,
                'partner_id': False,
                'product_qty': qty})
        inventory.action_done()
        return {
            'inventory_id': inventory.id,
            'date': inventory.date}
