# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, exceptions, fields, models, _


class BookingSettlement(models.Model):
    _name = 'booking.commission.settlement'
    _rec_name = 'agent'
    _order = 'date_from desc'

    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    total = fields.Float(
        compute='_compute_total',
        readonly=True,
        store=True,
    )
    date_from = fields.Date(
        string='From',
    )
    date_to = fields.Date(
        string='To',
    )
    agent = fields.Many2one(
        comodel_name='res.partner',
        domain="[('agent', '=', True)]",
    )
    agent_type = fields.Selection(
        related='agent.agent_type'
    )
    lines = fields.One2many(
        comodel_name='booking.commission.settlement.line',
        inverse_name='settlement',
        string='Settlement lines',
        readonly=True
    )
    state = fields.Selection(
        selection=[('settled', 'Settled'),
                   ('invoiced', 'Invoiced'),
                   ('cancel', 'Canceled'),
                   ('except_invoice', 'Invoice exception')],
        string='State',
        readonly=True,
        default='settled',
    )
    invoice = fields.Many2one(
        comodel_name='account.invoice',
        string='Generated invoice',
        readonly=True,
    )
    amount_untaxed = fields.Float(
        related='invoice.amount_untaxed',
    )
    amount_tax = fields.Float(
        related='invoice.amount_tax',
    )
    amount_total = fields.Float(
        related='invoice.amount_total',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        readonly=True,
        default=_default_currency,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company'
    )

    @api.depends('lines', 'lines.settled_amount')
    def _compute_total(self):
        for record in self:
            record.total = sum(x.settled_amount for x in record.lines)

    @api.one
    def action_recompute(self):
        for line in self.lines:
            line._compute_settled_amount()
        self._compute_total()

    @api.multi
    def action_cancel(self):
        if any(x.state != 'settled' for x in self):
            raise exceptions.Warning(_(
                'Cannot settled state in this state.'))
        self.write({'state': 'settled'})

    @api.multi
    def action_cancel_to_settled(self):
        if any(x.state != 'except_invoice' for x in self):
            raise exceptions.Warning(_(
                'Cannot cancel an invoiced settlement.'))
        self.write({'state': 'settled'})

    @api.multi
    def unlink(self):
        """Allow to delete only cancelled settlements"""
        if any(x.state == 'invoiced' for x in self):
            raise exceptions.Warning(
                _("You can't delete invoiced settlements."))
        return super(BookingSettlement, self).unlink()

    @api.multi
    def action_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Make invoice'),
            'res_model': 'booking.commission.make.invoice',
            'view_type': 'form',
            'target': 'new',
            'view_mode': 'form',
            'context': {'settlement_ids': self.ids}}

    def _prepare_invoice_header(self, settlement, journal, date=False):
        values = {
            'partner_id': settlement.agent.id,
            'type': journal.type == 'purchase' and 'in_invoice' or 'in_refund',
            'date_invoice': date,
            'journal_id': journal.id,
            'company_id': self.env.user.company_id.id,
            'reference': _('settlement'),
            'state': 'draft',
            'settlement_id': settlement.id}

        values.update(self.env['account.invoice'].onchange_partner_id(
            type=values['type'],
            partner_id=values['partner_id'],
            company_id=values['company_id'])['value'])
        return values

    def _prepare_invoice_line(self, settlement, values, product):
        line_value = {'product_id': product.id, 'quantity': 1}
        line_value.update(
            self.env['account.invoice.line'].product_id_change(
                product=line_value['product_id'],
                uom_id=False,
                type=values['type'],
                qty=line_value['quantity'],
                partner_id=values['partner_id'],
                fposition_id=values['fiscal_position'])
            ['value']
        )
        taxes = tuple(line_value['invoice_line_tax_id'])
        tax_id = (settlement.lines and
                  settlement.lines[0].invoice_line and
                  settlement.lines[0].invoice_line.commission_tax_id and
                  settlement.lines[0].invoice_line.commission_tax_id.id or
                  None)
        if tax_id:
            taxes = taxes + (tax_id,)
        line_value['invoice_line_tax_id'] = [(6, 0, taxes)]
        line_value['price_unit'] = settlement.total
        partner = self.env['res.partner'].browse(values['partner_id'])
        partner_lang = partner.lang or self.env.context.get('lang', 'en_US')
        lang = self.env['res.lang'].search([('code', '=', partner_lang)])
        date_from = fields.Date.from_string(settlement.date_from)
        date_to = fields.Date.from_string(settlement.date_to)
        line_value['name'] += '\n' + _('Period: from %s to %s') % (
            date_from.strftime(lang.date_format),
            date_to.strftime(lang.date_format))
        return line_value

    def _add_extra_invoice_lines(self, settlement):
        """Hook for adding extra invoice lines.
        :param settlement: Source settlement.
        :return: List of dictionaries with the extra lines.
        """
        return []

    @api.multi
    def make_invoices(self, journal, refund_journal, product, date=False):
        for settlement in self:
            extra_invoice_lines = self._add_extra_invoice_lines(settlement)
            extra_total = sum(x['price_unit'] for x in extra_invoice_lines)
            invoice_journal = (settlement.total + extra_total >= 0 and
                               journal or refund_journal)
            values = self._prepare_invoice_header(
                settlement, invoice_journal, date=date)
            lines_values = [
                self._prepare_invoice_line(settlement, values, product)]
            lines_values += extra_invoice_lines
            # invert invoice values if it's a refund
            if values['type'] == 'out_refund':
                for line in lines_values:
                    line['price_unit'] = -line['price_unit']
            values['invoice_line'] = [
                (0, 0, x) for x in lines_values]
            invoice = self.env['account.invoice'].create(values)
            invoice.button_reset_taxes()
            invoice.check_total = invoice.amount_total
            settlement.state = 'invoiced'
            settlement.invoice = invoice.id


class BookingSettlementLine(models.Model):
    _name = 'booking.commission.settlement.line'

    settlement = fields.Many2one(
        comodel_name='booking.commission.settlement',
        readonly=True,
        ondelete='cascade',
        required=True,
    )
    agent_line = fields.Many2many(
        comodel_name='account.invoice.line.agent',
        relation='settlement_agent_line_rel',
        column1='settlement_id',
        column2='agent_line_id',
        required=True,
    )
    date = fields.Date(
        related='agent_line.invoice_date',
        store=True,
    )
    invoice_line = fields.Many2one(
        comodel_name='account.invoice.line',
        store=True,
        related='agent_line.invoice_line',
    )
    invoice = fields.Many2one(
        comodel_name='account.invoice',
        store=True,
        string='Invoice',
        related='invoice_line.invoice_id',
    )
    agent = fields.Many2one(
        comodel_name='res.partner',
        readonly=True,
        related='agent_line.agent',
        store=True,
    )
    settled_amount = fields.Float(
        compute='_compute_settled_amount',
        readonly=True,
        store=True,
    )
    commission = fields.Many2one(
        comodel_name='booking.commission',
        related='agent_line.commission',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='settlement.company_id',
        store=True,
    )
    commission_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='commission tax',
    )

    @api.multi
    @api.depends('invoice_line', 'invoice')
    def _compute_settled_amount(self):
        for line in self:
            if line.invoice.type == 'out_refund':
                line.settled_amount = -line.agent_line.amount
            else:
                line.settled_amount = line.agent_line.amount
