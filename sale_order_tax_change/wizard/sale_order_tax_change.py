# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class WizSaleOrderTaxChange(models.TransientModel):
    _name = 'wiz.sale.order.tax.change'
    _description = 'Wizard sale order change tax'

    name = fields.Char(
        string='Empty')
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='sale_order_change_account_tax_rel',
        column1='change_tax_id',
        column2='tax_id')

    @api.multi
    def button_accept(self):
        order_ids = self.env.context.get('active_ids', [])
        for order in self.env['sale.order'].browse(order_ids):
            if order.state not in ['draft', 'sent']:
                raise exceptions.Warning(_(
                    'The order state must be \'Draft Quotation\' '
                    'or \'Quotation Sent\''))
            for line in order.order_line:
                for old_tax in line.tax_id:
                    line.write({'tax_id': [(3, old_tax.id)]})
                for new_tax in self.tax_ids:
                    line.write({'tax_id': [(4, new_tax.id)]})
        return {'type': 'ir.actions.act_window_close'}
