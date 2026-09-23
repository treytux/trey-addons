###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import UserError


class StockDeposit(models.TransientModel):
    _inherit = 'stock.deposit'

    def action_confirm(self):
        model_of_parent = self.env.context.get('active_model', False)
        if model_of_parent != 'vending.machine.move.stock.deposit':
            return super().action_confirm()
        machine_codes = self.env.context.get('machine_ids', [])
        date_from = self.env.context.get('date_from', False)
        last_date_stock_deposit = self.env.context.get(
            'last_date_stock_deposit', [])
        machines = self.env['vending.machine'].search([
            ('code', 'in', machine_codes),
        ])
        if not machines:
            raise UserError(_(
                'No vending machines found for the stock deposit.'))
        res = super().action_confirm()
        partner_names = ', '.join(
            [f'{machine.code}' for machine in machines])
        sale_order_id = res['domain'][0][2] or False
        sale_order = self.env['sale.order'].browse(sale_order_id)
        sale_order.client_order_ref = _(
            'Consumption %s, (%s) %s/%s') % (
            machines[0].partner_id.parent_name, partner_names, date_from,
            last_date_stock_deposit
        )
        for picking in sale_order.picking_ids:
            picking.client_order_ref = sale_order.client_order_ref
        sale_order.date_stock_deposit = last_date_stock_deposit
        sale_order.machine_ids = [(4, machine.id) for machine in machines]
        for machine in machines:
            machine._compute_last_date_stock_deposit()
        res['domain'] = [
            ('machine_ids', 'in', machines.ids),
            ('is_sale_deposit', '=', True),
        ]
        return res
