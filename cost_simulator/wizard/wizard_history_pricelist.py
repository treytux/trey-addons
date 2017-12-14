# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
import logging
_log = logging.getLogger(__name__)


class WizardHistoryPricelist(models.TransientModel):
    _name = 'wizard.history.pricelist'
    _description = 'Wizard Change Pricelist'

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        required=True,
        help="Pricelist for current sales order.")

    @api.one
    def button_ok(self):
        active_id = self.env.context.get('active_id', False)
        if active_id:
            cost_id = self.env['simulation.cost'].browse(active_id)
            cost_id.simulation_id.pricelist_id = self.pricelist_id
            cost_id.simulation_pricelist_id = self.pricelist_id
            for line in cost_id.simulation_line_ids:
                if line.lock_update_price:
                    continue
                res_sale = self.env['sale.order.line'].product_id_change(
                    pricelist=cost_id.simulation_pricelist_id.id,
                    product=line.product_id.id, qty=line.quantity or 0,
                    uom=line.product_id.uom_id.id or False, qty_uos=0,
                    uos=False, name='',
                    partner_id=line.cost_id.partner_id.id or False,
                    lang=False, update_tax=True,
                    date_order=False, packaging=False,
                    fiscal_position=False, flag=False)
                data = {'price': res_sale['value']['price_unit']}
                if 'discount' in res_sale['value']:
                    data['discount'] = res_sale['value']['discount']
                line.write(data)
            cost_id.simulation_id.compute_totals()
