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
        if 'agents' in res['value'] and 'agents' in self:
            updated_vals = []
            for agent_tuple in res['value']['agents']:
                agent_list = list(agent_tuple)[2]
                new_tup = True
                for agent in self.env['sale.order.line.agent'].sudo().search(
                        [('sale_line', '=', self.id)]):
                    if agent_list.get('agent') == agent.agent.id:
                        updated_vals.append((1, agent.id, agent_list))
                        new_tup = False
                if new_tup:
                    updated_vals.append(agent_tuple)
            res['value']['agents'] = updated_vals
        else:
            res['value']['agents'] = [(5,)]
        return res
