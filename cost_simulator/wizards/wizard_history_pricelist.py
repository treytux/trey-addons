###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class WizardHistoryPricelist(models.TransientModel):
    _name = 'wizard.history.pricelist'
    _description = 'Wizard Change Pricelist'

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        required=True,
        help='Pricelist for current sales order.',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
    )

    @api.multi
    def button_ok(self):
        SaleLine = self.env['sale.order.line']
        active_id = self.env.context.get('active_id', False)
        if active_id:
            cost_id = self.env['simulation.cost'].browse(active_id)
            cost_id.simulation_id.pricelist_id = cost_id.pricelist_id
            cost_id.simulation_pricelist_id = cost_id.pricelist_id
            for line in cost_id.simulation_line_ids:
                if line.lock_update_price:
                    continue
                discount = 0.0
                product_context = dict(
                    self.env.context,
                    partner_id=cost_id.partner_id.id,
                    date=cost_id.date, uom=line.product_id.uom_id.id)
                price, rule_id = cost_id.pricelist_id.with_context(
                    product_context).get_product_price_rule(
                    line.product_id, line.quantity, cost_id.partner_id)
                new_list_price, currency = SaleLine.with_context(
                    product_context)._get_real_price_currency(
                    line.product_id, rule_id, line.quantity,
                    line.product_id.uom_id, cost_id.pricelist_id.id)
                if new_list_price != 0:
                    if cost_id.pricelist_id.currency_id != currency:
                        new_list_price = currency._convert(
                            new_list_price, cost_id.pricelist_id.currency_id,
                            cost_id.company_id,
                            cost_id.date or fields.Date.today())
                        discount = \
                            (new_list_price - price) / new_list_price * 100
                line.write({
                    'price_sale': new_list_price,
                    'discount': discount,
                })
            cost_id.simulation_id.compute_totals()
