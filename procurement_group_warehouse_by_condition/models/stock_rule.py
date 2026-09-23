###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _run_pull(self, product_id, product_qty, product_uom, location_id,
                  name, origin, values):
        warehouse = values['warehouse_id']
        if not warehouse.is_warehouse_by_condition:
            return super()._run_pull(
                product_id, product_qty, product_uom, location_id, name,
                origin, values)
        condition_obj = self.env['procurement.group.warehouse_by_condition']
        condition = condition_obj.search([
            ('warehouse_id', '=', warehouse.id),
        ])
        partner = self.env['res.partner'].browse(values['partner_id'])
        sale = values.get('group_id', False) and values['group_id'].sale_id
        line = condition.get_condition_line(
            product_id, product_qty, partner.zip, sale)
        if not line:
            main_warehouse = self.env['stock.warehouse'].search([
                ('company_id', '=', self.company_id.id),
            ], limit=1)
            values.update({
                'warehouse_id': main_warehouse,
                'location_src_id': main_warehouse.lot_stock_id.id,
                'picking_type_id': main_warehouse.out_type_id.id,
            })
            return super()._run_pull(
                product_id, product_qty, product_uom, location_id, name,
                origin, values)
        values.update({
            'warehouse_id': line.main_warehouse_id,
            'location_src_id': line.main_warehouse_id.lot_stock_id.id,
            'picking_type_id': line.main_warehouse_id.out_type_id.id,
        })
        if not line.alternative_warehouse_ids:
            return super()._run_pull(
                product_id, product_qty, product_uom, location_id, name,
                origin, values)
        qty_available = product_id.with_context(
            warehouse=line.main_warehouse_id.id).qty_available
        if qty_available >= product_qty:
            return super()._run_pull(
                product_id, product_qty, product_uom, location_id, name,
                origin, values)
        elif qty_available > 0:
            super()._run_pull(
                product_id, qty_available, product_uom, location_id, name,
                origin, values)
        qty_pending = product_qty - qty_available
        for wh in line.alternative_warehouse_ids:
            if qty_pending == 0:
                return True
            wh_qty_available = product_id.with_context(
                warehouse=wh.id).qty_available
            if wh_qty_available == 0:
                continue
            wh_values = values.copy()
            wh_values.update({
                'warehouse_id': wh,
                'location_src_id': wh.lot_stock_id.id,
                'picking_type_id': wh.out_type_id.id,
            })
            qty = min(qty_pending, wh_qty_available)
            super()._run_pull(
                product_id, qty, product_uom, location_id, name, origin,
                wh_values)
            qty_pending -= qty
        if qty_pending == 0:
            return True
        return super()._run_pull(
            product_id, qty_pending, product_uom, location_id, name, origin,
            values)

    def _get_stock_move_values(self, product_id, product_qty, product_uom,
                               location_id, name, origin, values, group_id):
        data = super()._get_stock_move_values(
            product_id, product_qty, product_uom, location_id, name, origin,
            values, group_id)
        if values.get('location_src_id'):
            data['location_id'] = values['location_src_id']
        if values.get('warehouse_id'):
            data['warehouse_id'] = values['warehouse_id'].id
        if values.get('picking_type_id'):
            data['picking_type_id'] = values['picking_type_id']
        return data
