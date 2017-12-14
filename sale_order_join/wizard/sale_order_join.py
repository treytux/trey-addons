# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class SaleOrderJoin(models.TransientModel):
    _name = 'wiz.sale.order.join'
    _description = 'Wizard to join sale order'

    name = fields.Char(string='Empty')

    @api.multi
    def button_accept(self):
        sale_obj = self.env['sale.order']
        group_by_partner = {}
        partners_name = {}
        for sale in sale_obj.browse(self.env.context['active_ids']):
            if sale.state == 'draft':
                if sale.partner_id.id not in group_by_partner.keys():
                    group_by_partner[sale.partner_id.id] = []
                    partners_name[sale.partner_id.id] = sale.partner_id.name
                group_by_partner[sale.partner_id.id].append(sale)
            else:
                raise exceptions.Warning(_(
                    'Please check order states, wizard '
                    'will only join sale orders in draft state.'))
        for partner_id in group_by_partner.keys():
            sale_template = None
            sale_template_data = {}
            if len(group_by_partner[partner_id]) > 1:
                unlink_ids = []
                for sale in group_by_partner[partner_id]:
                    if not sale_template:
                        sale_template = sale
                        sale_template_data = {
                            'amount_total': 0,
                            'client_order_ref': sale.client_order_ref,
                            'note': ' ' + (
                                sale.note and sale.note.join('\n') or '')}
                        continue
                    else:
                        sale_template_data.update({'amount_total': 0})
                        if sale.client_order_ref:
                            sale_template_data.update({
                                'client_order_ref': ' ' + (
                                    sale_template_data.get(
                                        'client_order_ref', '') and
                                    sale.client_order_ref.join(
                                        '\n') or '')})
                        else:
                            sale_template_data.update({
                                'client_order_ref': sale_template_data.get(
                                    'client_order_ref', '')})
                        sale_template_data.update({
                            'note': (sale_template_data.get(
                                'note', '') + '\n') + sale.name or ''})
                    for line in sale.order_line:
                        line.order_id = sale_template.id
                    unlink_ids.append(sale.id)
                [sale_obj.browse(un).unlink() for un in unlink_ids]
                sale_obj.write({
                    'order_id': sale_template.id,
                    'amount_total': sale_template_data['amount_total'],
                    'client_order_ref': sale_template_data['client_order_ref'],
                    'note': sale_template_data['note']})
                if sale_template:
                    sale_template.recalculate_prices()
            else:
                raise exceptions.Warning(_(
                    'Only %s selected sales order for the partner %s.' % (
                        len(group_by_partner[partner_id]),
                        partners_name[partner_id])))
        return {'type': 'ir.actions.act_window_close'}
