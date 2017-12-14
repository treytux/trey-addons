# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False):
        res = super(SaleOrderLine, self).product_id_change(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
            date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag)
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
