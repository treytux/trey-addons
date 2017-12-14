# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class WizPurchaseOrderTaxChange(models.TransientModel):
    _name = 'wiz.purchase.order.tax.change'
    _description = 'Wizard purchase order change tax'

    name = fields.Char(
        string='Empty')
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='purchase_order_change_account_tax_rel',
        column1='change_tax_id',
        column2='tax_id')

    @api.one
    def button_accept(self):
        new_taxs = [(4, t.id) for t in self.tax_ids]
        order_ids = self.env.context.get('active_ids', [])
        for order in self.env['purchase.order'].browse(order_ids):
            if order.state not in ['draft', 'sent']:
                raise exceptions.Warning(_(
                    'The order state must be \'Draft PO\' '
                    'or \'RFQ\''))
            for line in order.order_line:
                old_taxs = [(3, t.id) for t in line.taxes_id]
                line.write({'taxes_id': old_taxs + new_taxs})
        return {'type': 'ir.actions.act_window_close'}
