###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _get_sale_origins_from_procurement_origin(self, origin):
        if not origin:
            return []
        if ' - ' in origin:
            origin = origin.rsplit(' - ', 1)[1]
        return [item.strip() for item in origin.split(',') if item.strip()]

    @api.model
    def _get_sale_line_from_procurement(self, procurement):
        values = procurement.values
        sale_line_obj = self.env['sale.order.line']
        if values.get('move_dest_ids'):
            sale_lines = values['move_dest_ids'].mapped('sale_line_id')
            if sale_lines:
                return sale_lines[:1]
        if values.get('sale_line_id'):
            return sale_line_obj.browse(values['sale_line_id'])
        orderpoint = values.get('orderpoint_id')
        if not orderpoint:
            return sale_line_obj
        sale_origins = self._get_sale_origins_from_procurement_origin(
            procurement.origin)
        if not sale_origins:
            return sale_line_obj
        domain = [
            ('company_id', '=', procurement.company_id.id),
            ('order_id.name', 'in', sale_origins),
            ('order_id.state', 'in', ['sale', 'done']),
            ('product_id', '=', procurement.product_id.id),
            ('supplierinfo_id', '!=', False),
        ]
        if orderpoint.warehouse_id:
            domain.append(
                ('order_id.warehouse_id', '=', orderpoint.warehouse_id.id))
        sale_lines = sale_line_obj.search(domain, order='id desc')
        supplierinfos = sale_lines.mapped('supplierinfo_id')
        if len(supplierinfos) == 1:
            return sale_lines.filtered(
                lambda line: line.supplierinfo_id == supplierinfos)[:1]
        return sale_line_obj

    @api.model
    def _run_buy(self, procurements):
        for procurement, _rule in procurements:
            sale_line = self._get_sale_line_from_procurement(procurement)
            if sale_line:
                procurement.values['supplierinfo_id'] = (
                    sale_line.supplierinfo_id)
        return super()._run_buy(procurements)

    def _is_dropship_route(self, route_ids):
        if not route_ids:
            return False
        return bool(route_ids.rule_ids.filtered(
            lambda r: r.action == 'buy'
            and r.location_src_id.usage == 'supplier'
            and r.location_dest_id.usage == 'customer'
        ))

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super()._make_po_get_domain(company_id, values, partner)
        sale_line = self.env['sale.order.line'].browse(
            values.get('sale_line_id'))
        sale_line_route_is_dropship = (
            sale_line.route_id and self._is_dropship_route(sale_line.route_id))
        product_has_dropship = (
            not sale_line.route_id and self._is_dropship_route(
                sale_line.product_id.route_ids))
        if sale_line and sale_line_route_is_dropship or product_has_dropship:
            return domain
        return tuple(
            item for item in domain
            if not (isinstance(item, tuple) and item[0] == 'group_id')
        )
