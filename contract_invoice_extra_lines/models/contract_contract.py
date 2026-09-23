###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import Command, fields, models


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    contract_line_extra_ids = fields.One2many(
        string='Contract lines extra',
        comodel_name='contract.line.extra',
        inverse_name='contract_id',
        copy=True,
    )

    def _get_lines_extra_to_invoice(self, date_ref):
        self.ensure_one()

        def can_be_invoiced(contract_line_extra):
            return (
                not contract_line_extra.invoice_id
                and contract_line_extra.date_to_invoice
                and contract_line_extra.date_to_invoice <= date_ref
            )

        lines_extra_to_invoice = self.env['contract.line.extra']
        for line in self.contract_line_extra_ids:
            if can_be_invoiced(line):
                lines_extra_to_invoice |= line
        return lines_extra_to_invoice.sorted()

    def _prepare_recurring_invoices_values(self, date_ref=False):
        invoices_values = super()._prepare_recurring_invoices_values()
        for contract in self:
            if not date_ref:
                date_ref = contract.recurring_next_date
            if not date_ref:
                continue
            contract_lines_extra = contract._get_lines_extra_to_invoice(
                date_ref)
            if not contract_lines_extra:
                continue
            if not invoices_values:
                continue
            invoice_vals = invoices_values[0]
            for line in contract_lines_extra:
                invoice_line_vals = line._prepare_invoice_line()
                if invoice_line_vals:
                    invoice_vals['invoice_line_ids'].append(
                        Command.create(invoice_line_vals)
                    )
        return invoices_values

    def _recurring_create_invoice(self, date_ref=False):
        moves = super()._recurring_create_invoice(date_ref=date_ref)
        if not moves:
            return moves
        contract_lines_extra = moves.invoice_line_ids.filtered(
            lambda ml: ml.contract_line_extra_id).mapped(
                'contract_line_extra_id')
        for contract_line_extra in contract_lines_extra:
            contract_line_extra.invoice_id = moves[0].id
        return moves
