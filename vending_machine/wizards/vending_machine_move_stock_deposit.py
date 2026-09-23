###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class VendingMachineMoveStockDeposit(models.TransientModel):
    _name = 'vending.machine.move.stock.deposit'
    _description = 'Vending Machine Move Stock Deposit'

    @api.model
    def _default_date_from(self):
        today = fields.Date.today()
        first_of_this_month = today.replace(day=1)
        last_month = first_of_this_month - datetime.timedelta(days=1)
        date_from = last_month.replace(day=1)
        vending_id = self.env.context.get('vending_machine_id')
        vending_machine = self.env['vending.machine'].browse(
            vending_id).exists()
        if not vending_machine:
            raise UserError(_('Vending machine not found.'))
        last_date_stock_deposit = vending_machine.last_date_stock_deposit
        if last_date_stock_deposit and date_from <= last_date_stock_deposit:
            date_from = last_date_stock_deposit + datetime.timedelta(days=1)
        return date_from

    def _default_date_to(self):
        today = fields.Date.today()
        first_of_this_month = today.replace(day=1)
        last_of_previous_month = first_of_this_month - datetime.timedelta(
            days=1)
        vending_id = self.env.context.get('vending_machine_id')
        vending_machine = self.env['vending.machine'].browse(
            vending_id).exists()
        if not vending_machine:
            raise UserError(_('Vending machine not found.'))
        last_date_stock_deposit = vending_machine.last_date_stock_deposit
        if (last_date_stock_deposit
                and last_of_previous_month <= last_date_stock_deposit):
            last_of_next_date_stock_deposit = (
                (last_date_stock_deposit + datetime.timedelta(days=32)
                 ).replace(day=1) - datetime.timedelta(days=1))
            last_of_previous_month = last_of_next_date_stock_deposit
        return last_of_previous_month

    vending_machine_id = fields.Many2one(
        comodel_name='vending.machine',
        required=True,
    )
    date_from = fields.Date(
        string='Date From',
        default=_default_date_from,
    )
    date_to = fields.Date(
        string='Date To',
        default=_default_date_to,
    )

    def action_move_stock(self):
        self.ensure_one()
        if not self.date_from or not self.date_to:
            raise UserError(_('Please provide a valid date range.'))
        return self.vending_machine_id.action_move_to_deposit(
            date_from=self.date_from,
            date_to=self.date_to,
        )

    @api.multi
    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        if self.date_from > self.date_to:
            raise UserError(_(
                '"Date To" cannot be earlier than the last stock deposit date '
                'of the vending machine.'))

        last_date_stock_deposit = (
            self.vending_machine_id.last_date_stock_deposit)
        if last_date_stock_deposit and self.date_to <= last_date_stock_deposit:
            raise UserError(_(
                '"Date To" cannot be earlier than the last stock deposit date '
                'of the vending machine.')
            )
        if last_date_stock_deposit and self.date_from <= last_date_stock_deposit:
            raise UserError(_(
                '"Date From" cannot be earlier than the last stock deposit '
                'date of the vending machine. Set it to %s.') % (
                    last_date_stock_deposit + datetime.timedelta(days=1))
            )
