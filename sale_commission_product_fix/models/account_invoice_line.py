# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def product_id_change(
            self, product, uom_id, qty=0, name='',
            type='out_invoice', partner_id=False, fposition_id=False,
            price_unit=False, currency_id=False, company_id=None):
        res = super(AccountInvoiceLine, self).product_id_change(
            product, uom_id, qty, name, type, partner_id,
            fposition_id, price_unit, currency_id, company_id)
        if self.agents and res.get('value') and res['value'].get('agents'):
            updated_vals = []
            tupples = res['value']['agents']
            for tup in tupples:
                list_tup = list(tup)
                new_tup = True
                for agent in self.agents:
                    if list_tup[2].get('agent') == agent.agent.id:
                        updated_vals.append((1, agent.id, list_tup[2]))
                        new_tup = False
                if new_tup:
                    updated_vals.append(tup)
            res['value']['agents'] = updated_vals
        if self.agents and res.get('value') and not res['value'].get('agents'):
            res['value']['agents'] = [(5,)]
        return res
