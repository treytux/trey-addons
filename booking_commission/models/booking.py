# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models


class Booking(models.Model):
    _inherit = "booking"

    amount_commission = fields.Float(
        string="Commissions")
    booking_net_price = fields.Float(
        string="Net",
        help="Booking net price")


class BookingLine(models.Model):
    _inherit = "booking.line"

    agents = fields.One2many(
        string="Agents & commissions",
        comodel_name='booking.line.agent',
        inverse_name='booking_line',
        copy=True)
    commission_amount_tax = fields.Float(
        string="Commision amount tax")
    commission_amount = fields.Float(
        string='Commission amount')
    commission_percentage_tax = fields.Float(
        string='Commission percentage tax')
    commission_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='commission tax')


class BookingLineAgent(models.Model):
    _name = "booking.line.agent"
    _rec_name = "agent"

    @api.depends('booking_line.cost_net', 'booking_line.cost_gross')
    def _compute_amount(self):
        #  REVISAR
        for line in self:
            line.amount = 0.0
            if line.commission:
                if line.commission.commission_type == 'fixed':
                    line.amount = line.booking_line.commission_amount

    booking_line = fields.Many2one(
        comodel_name="booking.line",
        required=True,
        ondelete="cascade")
    agent = fields.Many2one(
        comodel_name="res.partner",
        required=True,
        ondelete="restrict",
        domain="[('agent', '=', True')]")
    commission = fields.Many2one(
        comodel_name="booking.commission",
        required=True,
        ondelete="restrict")
    amount = fields.Float(
        compute="_compute_amount",
        store=True)

    _sql_constraints = [
        ('unique_agent', 'UNIQUE(booking_line, agent)',
         'You can only add one time each agent.')
    ]

    @api.onchange('agent')
    def onchange_agent(self):
        self.commission = self.agent.commission
