# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _
from functools import partial
import math


class ReportPrintFormatsPickingValued(models.TransientModel):
    _name = 'report.print_formats_picking_valued.report_picking_valued'

    def get_lines_from_operations(self, operations):
        moves = []
        for op in operations:
            moves += [(m.move_id, op) for m in op.linked_move_operation_ids]
        return tuple(set(moves))

    @api.model
    def get_lines(self, picking):
        if picking.pack_operation_ids:
            return self.get_lines_from_operations(picking.pack_operation_ids)
        return [(m, None) for m in picking.move_lines]

    @api.model
    def get_prices(self, line):
        def _get_pricelist(move):
            pricelist = None
            if move.picking_id.sale_id:
                pricelist = move.picking_id.sale_id.pricelist_id
            if move.purchase_line_id.exists():
                pricelist = move.purchase_line_id.order_id.pricelist_id
            if (move.picking_id.partner_id and
                    move.picking_id.partner_id.property_product_pricelist):
                pricelist = (
                    move.picking_id.partner_id.property_product_pricelist)
            return pricelist

        move, operation = line
        qty = operation and operation.product_qty or move.product_uom_qty
        res = {
            'qty': qty,
            'price_unit': 0.,
            'price_subtotal': 0.,
            'price_taxes': 0.,
            'discount': 0.,
            'pricelist_id': None}
        sale_line = self.get_sale_line(move)
        if sale_line:
            res.update({
                'qty': qty,
                'price_unit': sale_line.price_unit,
                'price_subtotal': ((
                    sale_line.price_subtotal / sale_line.product_uom_qty) *
                    qty),
                'price_taxes': ((
                    sale_line.order_id._amount_line_tax(sale_line) /
                    sale_line.product_uom_qty) * qty),
                'discount': sale_line.discount,
                'pricelist_id': sale_line.order_id.pricelist_id})
            return res
        pricelist = _get_pricelist(move)
        if not pricelist:
            raise exceptions.Warning(_('There is not pricelist'))
        return pricelist.price_get(
            move.product_id.id, qty,
            move.picking_id.partner_id.id)[pricelist.id]

    def get_sale_line(self, move):
        return (
            move.procurement_id and move.procurement_id.sale_line_id or None)

    def get_pricelist(self, picking):
        if picking.sale_id.exists():
            return picking.sale_id.pricelist_id
        if picking.partner_id.exists():
            return picking.partner_id.property_product_pricelist
        return None

    def get_order_line_from_pack_operation(self, pack_operation):
        return (
            pack_operation and pack_operation.linked_move_operation_ids and
            pack_operation.linked_move_operation_ids[0].move_id and
            self.get_order_line_from_move(
                pack_operation.linked_move_operation_ids[0].move_id) or None)

    def monetary_format(self, amount):
        cr, uid, context = self.env.args
        company = self.env['res.company'].search([])[0]
        currency = company.currency_id
        lang_code = context.get('lang') or 'en_US'
        lang = self.env['res.lang'].search([('code', '=', lang_code)])
        precision = int(round(math.log10(currency.rounding)))
        fmt = "%.{0}f".format(-precision if precision < 0 else 0)
        formatted_amount = lang.format(
            fmt, currency.round(amount), grouping=True, monetary=True)
        return formatted_amount

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        template = 'print_formats_picking_valued.report_picking_valued'
        doc = report_obj._get_report_from_name(template)
        report = report_obj.browse(self.ids[0])
        return report.render(template, {
            'doc_ids': self.ids,
            'doc_model': doc.model,
            'docs': self.env['stock.picking'].browse(self.ids),
            'get_lines': self.get_lines,
            'get_prices': self.get_prices,
            'get_pricelist': partial(self.get_pricelist),
            'monetary_format': partial(self.monetary_format),
        })
