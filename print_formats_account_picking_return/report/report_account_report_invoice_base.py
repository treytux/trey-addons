###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from types import SimpleNamespace

from odoo import api, models


class ReportAccountReportInvoiceBase(models.AbstractModel):
    _inherit = 'report.account.report_invoice_base'

    def get_invoice_lines(self, invoice):
        return invoice.invoice_line_ids

    def get_values_to_no_picking(self, invoice_line):
        move = SimpleNamespace(
            product_id=invoice_line.product_id,
            weight_uom_id=invoice_line.product_id.uom_id,
            sale_discount=invoice_line.discount
        )
        price_with_discount = (
            (invoice_line.price_subtotal / invoice_line.quantity)
            if invoice_line.quantity else 0)
        return {
            'picking': False,
            'line': invoice_line,
            'move': move,
            'price_subtotal': invoice_line.price_subtotal,
            'price_unit': price_with_discount,
            'price_total': invoice_line.price_total,
            'quantity': invoice_line.quantity,
        }

    def get_data_from_move(self, move, invoice_lines):
        code = move.picking_id.picking_type_id.code
        incoming = code == 'incoming'
        product_id = move.product_id
        current_invoice_lines = invoice_lines.filtered(
            lambda line: line.product_id == product_id
            and move.sale_line_id in line.sale_line_ids)
        discount = (
            (current_invoice_lines and current_invoice_lines[0].discount)
            or move.sale_line_id.discount)
        price_unit = (
            ((current_invoice_lines and current_invoice_lines[0].price_unit)
             or move.sale_line_id.price_unit)
            * (1 - (discount or 0.0) / 100.0))
        quantity_done = move.quantity_done
        product_uom_qty = move.sale_line_id.product_uom_qty
        price_subtotal = (
            (current_invoice_lines
             and ((current_invoice_lines[0].price_subtotal
                   / current_invoice_lines[0].quantity
                   if current_invoice_lines[0].quantity else 0)
                  * quantity_done))
            or ((move.sale_line_id.price_subtotal / product_uom_qty
                 if move.sale_line_id.price_subtotal else 0)
                * (quantity_done or product_uom_qty)))
        price_total = (
            (current_invoice_lines
             and ((current_invoice_lines[0].price_total
                   / current_invoice_lines[0].quantity
                   if current_invoice_lines[0].quantity else 0)
                  * quantity_done))
            or ((move.sale_line_id.price_total / product_uom_qty
                 if move.sale_line_id.price_total else 0)
                * (quantity_done or product_uom_qty)))
        remaining_qty = (
            product_uom_qty - move.sale_line_id.qty_delivered)
        return {
            'incoming': incoming,
            'product_id': product_id,
            'price_unit': price_unit,
            'quantity_done': quantity_done,
            'product_uom_qty': product_uom_qty,
            'price_subtotal': price_subtotal,
            'price_total': price_total,
            'remaining_qty': remaining_qty,
        }

    def get_lines_grouped(self, invoice):
        original_res = super().get_lines_grouped(invoice)
        res = []
        no_picking = []
        sales_already_processed = self.env['sale.order']
        not_group_by = not invoice.company_id.invoice_report_group_by
        invoice_lines = self.get_invoice_lines(invoice)
        for invoice_line in invoice_lines:
            sale_orders = invoice_line.mapped('sale_line_ids.order_id')
            if not sale_orders:
                no_picking.append(self.get_values_to_no_picking(
                    invoice_line))
                continue
            elif sale_orders in sales_already_processed:
                continue
            sales_already_processed |= sale_orders
            moves_of_sale_orders = self.env['stock.move'].search([
                ('sale_line_id.order_id', 'in', sale_orders.ids),
            ]).sorted(key=lambda m: m.id)
            moves_of_sale_orders = moves_of_sale_orders.filtered(
                lambda move: move.state == 'done')
            for move in moves_of_sale_orders:
                data_move = self.get_data_from_move(move, invoice_lines)
                incoming = data_move['incoming']
                product_id = data_move['product_id']
                price_unit = data_move['price_unit']
                quantity_done = data_move['quantity_done']
                product_uom_qty = data_move['product_uom_qty']
                price_subtotal = data_move['price_subtotal']
                price_total = data_move['price_total']
                remaining_qty = data_move['remaining_qty']
                if remaining_qty > 0 and product_id.invoice_policy == 'order':
                    product_already_in_no_picking = any(
                        item['move'].product_id.id == product_id.id
                        for item in no_picking
                    )
                    if not product_already_in_no_picking:
                        no_picking.append({
                            'picking': False,
                            'line': invoice_line,
                            'move': move,
                            'price_subtotal': (
                                price_subtotal
                                / (quantity_done or product_uom_qty)
                                * remaining_qty),
                            'price_unit': price_unit,
                            'price_total': (
                                price_total
                                / (quantity_done or product_uom_qty)
                                * remaining_qty),
                            'quantity': remaining_qty,
                        })
                order_id = move.sale_line_id.order_id
                previous_invoice = order_id.invoice_ids.filtered(
                    lambda inv: inv.id < invoice.id
                ).sorted(key=lambda inv: inv.id)[-1:]
                if (quantity_done > 0
                    and (not previous_invoice or move.picking_id.date_done
                         > previous_invoice.create_date)
                        and (move.picking_id.date_done
                             <= invoice.create_date)):
                    res.append({
                        'picking': (False if not_group_by
                                    else move.picking_id),
                        'line': invoice_line,
                        'move': move,
                        'price_subtotal': (
                            incoming and -price_subtotal or price_subtotal),
                        'price_unit': (
                            incoming and -price_unit or price_unit),
                        'price_total': (
                            incoming and -price_total or price_total),
                        'quantity': (
                            incoming and -quantity_done or quantity_done)})
        data_to_send = no_picking + res
        correct_data = self.check_data_to_send(
            data_to_send, invoice_lines, invoice)
        if not data_to_send or not correct_data:
            return self._normal_flow(original_res)
        return data_to_send

    def _normal_flow(self, original_res):
        for line in original_res:
            invoice_line = line['line']
            quantity = line['quantity']
            price_unit_with_discount = (
                invoice_line.price_subtotal / invoice_line.quantity
                if invoice_line.quantity else 0)
            if invoice_line.move_line_ids:
                line['move'] = invoice_line.move_line_ids[0]
            else:
                move = SimpleNamespace(
                    product_id=invoice_line.product_id,
                    weight_uom_id=invoice_line.product_id.uom_id,
                    sale_discount=invoice_line.discount
                )
                line['move'] = move
            line['price_unit'] = price_unit_with_discount
            line['price_subtotal'] = (
                quantity * (invoice_line.price_subtotal / invoice_line.quantity
                            if invoice_line.quantity else 0))
            line['price_total'] = (
                quantity * (invoice_line.price_total / invoice_line.quantity
                            if invoice_line.quantity else 0))
        return original_res

    def check_data_to_send(self, data_to_send, invoice_lines, invoice):
        is_complete = not bool(any(
            move not in [data['move'] for data in data_to_send]
            for move in invoice_lines.mapped('move_line_ids')))
        correct_amount_untaxed = invoice.amount_untaxed == round(sum(
            line['price_subtotal'] for line in data_to_send), 2)
        correct_amount_tax = invoice.amount_tax == round(sum(
            line['price_total'] - line['price_subtotal']
            for line in data_to_send), 2)
        correct_amount_total = invoice.amount_total == round(sum(
            line['price_total'] for line in data_to_send), 2)
        return (
            is_complete and correct_amount_untaxed and correct_amount_tax
            and correct_amount_total)

    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.invoice'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'account.invoice',
            'docs': docs,
            'get_lines_grouped': self.get_lines_grouped,
            'show_qty_column': self.show_qty_column,
            'get_payment_terms': self.get_payment_terms,
        }


class ReportAccountReportInvoice(ReportAccountReportInvoiceBase):
    _inherit = 'report.account.report_invoice'


class ReportAccountReportInvoiceWithPayments(ReportAccountReportInvoiceBase):
    _inherit = 'report.account.report_invoice_with_payments'
