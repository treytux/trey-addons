###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _run_pull(self, procurements):
        for procurement, rule in procurements:
            warehouse = procurement.values['warehouse_id']
            if not warehouse.is_warehouse_by_condition:
                super()._run_pull([(procurement, rule)])
                continue
            condition_obj = (
                self.env['procurement.group.warehouse_by_condition'])
            condition = condition_obj.search([
                ('warehouse_id', '=', warehouse.id),
            ])
            partner = self.env['res.partner'].browse(
                procurement.values['partner_id'])
            sale = (
                procurement.values.get('group_id', False)
                and procurement.values['group_id'].sale_id)
            line = condition.get_condition_line(
                procurement.product_id, procurement.product_qty, partner.zip,
                sale)
            if not line:
                main_warehouse = self.env['stock.warehouse'].search([
                    ('company_id', '=', rule.company_id.id),
                ], limit=1)
                procurement.values.update({
                    'warehouse_id': main_warehouse,
                    'location_src_id': main_warehouse.lot_stock_id.id,
                    'picking_type_id': main_warehouse.out_type_id.id,
                })
                super()._run_pull([(procurement, rule)])
                continue
            old_product_qty = procurement.product_qty
            procurement.values.update({
                'warehouse_id': line.main_warehouse_id,
                'location_src_id': line.main_warehouse_id.lot_stock_id.id,
                'picking_type_id': line.main_warehouse_id.out_type_id.id,
            })
            if not line.alternative_warehouse_ids:
                super()._run_pull([(procurement, rule)])
                continue
            quantity = self.env.user.company_id.product_qty_field
            qty_field_available = procurement.product_id.with_context(
                warehouse=line.main_warehouse_id.id)[quantity]
            if qty_field_available >= procurement.product_qty:
                super()._run_pull([(procurement, rule)])
                continue
            elif qty_field_available > 0:
                procurement = procurement._replace(product_qty=qty_field_available)
                super()._run_pull([(procurement, rule)])
            qty_pending = old_product_qty - qty_field_available
            for wh in line.alternative_warehouse_ids:
                if qty_pending == 0:
                    continue
                wh_qty_field_available = procurement.product_id.with_context(
                    warehouse=wh.id)[quantity]
                if wh_qty_field_available <= 0:
                    continue
                qty = min(qty_pending, wh_qty_field_available)
                procurement = procurement._replace(product_qty=qty)
                procurement.values.update({
                    'warehouse_id': wh,
                    'location_src_id': wh.lot_stock_id.id,
                    'picking_type_id': wh.out_type_id.id,
                })
                super()._run_pull([(procurement, rule)])
                qty_pending -= qty
            if qty_pending == 0:
                continue
            procurement = procurement._replace(product_qty=qty_pending)
            procurement.values.update({
                'warehouse_id': line.main_warehouse_id,
                'location_src_id': line.main_warehouse_id.lot_stock_id.id,
                'picking_type_id': line.main_warehouse_id.out_type_id.id,
            })
            super()._run_pull([(procurement, rule)])
        return True

    def _get_stock_move_values(
            self, product_id, product_qty, product_uom, location_dest_id, name,
            origin, company_id, values):
        data = super()._get_stock_move_values(
            product_id, product_qty, product_uom, location_dest_id, name,
            origin, company_id, values)
        if values.get('location_src_id'):
            data['location_id'] = values['location_src_id']
        if values.get('warehouse_id'):
            data['warehouse_id'] = values['warehouse_id'].id
        if values.get('picking_type_id'):
            data['picking_type_id'] = values['picking_type_id']
        return data
