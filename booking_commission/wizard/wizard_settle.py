# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class BookingCommissionMakeSettle(models.TransientModel):
    _name = "booking.commission.make.settle"

    date_to = fields.Date(
        'Up to',
        required=True,
        default=fields.Date.today())
    agents = fields.Many2many(
        comodel_name='res.partner',
        domain="[('agent', '=', True)]")

    def _get_period_start(self, agent, date_to):
        if isinstance(date_to, basestring):
            date_to = fields.Date.from_string(date_to)
        if agent.settlement == 'monthly':
            return date(month=date_to.month, year=date_to.year, day=1)
        elif agent.settlement == 'quaterly':
            # Get first month of the date quarter
            month = ((date_to.month - 1) // 3 + 1) * 3
            return date(month=month, year=date_to.year, day=1)
        elif agent.settlement == 'semi':
            if date_to.month > 6:
                return date(month=7, year=date_to.year, day=1)
            else:
                return date(month=1, year=date_to.year, day=1)
        elif agent.settlement == 'annual':
            return date(month=1, year=date_to.year, day=1)
        else:
            raise exceptions.Warning(_("Settlement period not valid."))

    def _get_next_period_date(self, agent, current_date):
        if isinstance(current_date, basestring):
            current_date = fields.Date.from_string(current_date)
        if agent.settlement == 'monthly':
            return current_date + relativedelta(months=1)
        elif agent.settlement == 'quaterly':
            return current_date + relativedelta(months=3)
        elif agent.settlement == 'semi':
            return current_date + relativedelta(months=6)
        elif agent.settlement == 'annual':
            return current_date + relativedelta(years=1)
        else:
            raise exceptions.Warning(_("Settlement period not valid."))

    @api.multi
    def action_settle(self):
        self.ensure_one()
        # agent_line_obj = self.env['account.invoice.line.agent']
        # settlement_obj = self.env['booking.commission.settlement']
        # settlement_line_obj = self.env['booking.commission.settlement.line']
        settlement_ids = []
        sett_to = fields.Date.to_string(date(year=1900, month=1, day=1))
        if not self.agents:
            self.agents = self.env['res.partner'].search(
                [('agent', '=', True)])
        for agent in self.agents:
            agent_lines = self.env['account.invoice.line.agent'].search([
                ('agent', '=', agent.id),
                ('settled', '=', False),
                ('invoice.type', 'in', ('out_invoice', 'out_refund'))],
                order='invoice_date')
            if not agent_lines:
                continue
            for company in agent_lines.mapped('invoice_line.company_id'):
                agent_lines_company = agent_lines.filtered(
                    lambda agent_l: agent_l.invoice_line.company_id == company)
                if not agent_lines_company:
                    continue
                for agent_line in agent_lines_company:
                    agent_line_not_paid = (agent_line.invoice.state != 'paid')
                    if agent.commission.invoice_state == 'paid' and \
                            agent_line_not_paid:
                        continue
                    if agent_line.invoice_date <= sett_to:
                        continue
                    # if agent_line.invoice_date > sett_to:
                    sett_from = self._get_period_start(
                        agent, agent_line.invoice_date)
                    sett_to = fields.Date.to_string(self._get_next_period_date(
                        agent, sett_from) - timedelta(days=1))
                    sett_from = fields.Date.to_string(sett_from)
                    settlement = self.env[
                        'booking.commission.settlement'].create({
                            'agent': agent.id,
                            'date_from': sett_from,
                            'date_to': sett_to,
                            'company_id': company.id,
                        })
                    settlement_ids.append(settlement.id)
                    invoice_line = agent_line.invoice_line
                    self.env['booking.commission.settlement.line'].create({
                        'settlement': settlement.id,
                        'agent_line': [(6, 0, [agent_line.id])],
                        'commission_tax_id': (
                            invoice_line.commission_tax_id and
                            invoice_line.commission_tax_id.id or None),
                    })
        if len(settlement_ids):
            return {
                'name': _('Created Settlements'),
                'type': 'ir.actions.act_window',
                'views': [[False, 'list'], [False, 'form']],
                'res_model': 'booking.commission.settlement',
                'domain': [['id', 'in', settlement_ids]],
            }
        else:
            return {'type': 'ir.actions.act_window_close'}
