# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_lines_massive_edit(self):
        self.ensure_one()
        wiz = self.env['wiz.invoice_lines_edit'].create({})
        for line in self[0].invoice_line:
            self.env['wiz.invoice_lines_edit.lines'].create({
                'wizard_id': wiz.id,
                'line_id': line.id,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'discount': line.discount})
        view = self.env.ref(
            'account_invoice_lines_massive_edit.wiz_invoice_lines_edit')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wiz.invoice_lines_edit',
            'res_id': wiz.id,
            'view_id': view.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new'}
