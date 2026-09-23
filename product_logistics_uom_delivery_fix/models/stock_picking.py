##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_move_converted_weight(self, move, qty_field):
        self.ensure_one()
        default_weight_uom = self.env[
            'product.template']._get_weight_uom_id_from_ir_config_parameter()
        qty = move.product_uom._compute_quantity(
            getattr(move, qty_field, 0.0), move.product_id.uom_id, round=False)
        from_uom = move.product_id.weight_uom_id or default_weight_uom
        to_uom = self.weight_uom_id or default_weight_uom
        unit_weight = from_uom._compute_quantity(
            move.product_id.weight, to_uom, round=False)
        return qty * unit_weight

    @api.depends(
        'move_ids_without_package', 'move_ids_without_package.product_uom_qty',
        'move_ids_without_package.quantity_done',
        'move_ids_without_package.reserved_availability', 'weight_uom_id')
    def _cal_weight(self):
        def _determine_qty_field(picking):
            field = 'product_uom_qty'
            for opt_field in ['quantity_done', 'reserved_availability']:
                has = any(
                    picking.mapped('move_ids_without_package.' + opt_field))
                if has:
                    return opt_field
            return field

        with_pack_ops = self.filtered('move_ids_without_package')
        for picking in with_pack_ops:
            field = _determine_qty_field(picking)
            picking.weight = sum(
                picking._get_move_converted_weight(move, field)
                for move in picking.move_ids_without_package)
        super(StockPicking, self - with_pack_ops)._cal_weight()

    @api.one
    @api.depends(
        'move_line_ids', 'move_line_ids.product_id',
        'move_line_ids.product_uom_id', 'move_line_ids.qty_done',
        'move_line_ids.result_package_id', 'weight_uom_id')
    def _compute_bulk_weight(self):
        super()._compute_bulk_weight()
        default_weight_uom = self.env[
            'product.template']._get_weight_uom_id_from_ir_config_parameter()
        weight = 0.0
        to_uom = self.weight_uom_id or default_weight_uom
        for move_line in self.move_line_ids:
            if not move_line.product_id or move_line.result_package_id:
                continue
            qty = move_line.product_uom_id._compute_quantity(
                move_line.qty_done, move_line.product_id.uom_id, round=False)
            from_uom = move_line.product_id.weight_uom_id or default_weight_uom
            unit_weight = from_uom._compute_quantity(
                move_line.product_id.weight, to_uom, round=False)
            weight += qty * unit_weight
        self.weight_bulk = weight
