# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models


class BasePartnerMergeAutomaticWizard(models.TransientModel):
    _inherit = 'base.partner.merge.automatic.wizard'

    change_account_invoice_and_move = fields.Boolean(
        string='Change account invoices and moves',
    )
    destination_partner_id = fields.Integer(
        string='Destination Partner ID',
    )

    @api.onchange('dst_partner_id')
    def onchange_dst_partner_id(self):
        if not self.dst_partner_id:
            return
        self.destination_partner_id = self.dst_partner_id.id

    @api.one
    def action_change_account_invoice_and_move(self):
        source_partner_ids = list(
            set(self.partner_ids.ids) ^ set(self.dst_partner_id.ids))
        invoices = self.env['account.invoice'].search([
            ('partner_id', 'in', source_partner_ids)])
        move_lines = self.env['account.move.line'].search([
            ('partner_id', 'in', self.partner_ids._ids)])
        for invoice in invoices:
            invoice.partner_id = self.dst_partner_id
        for line in move_lines:
            line.partner_id = self.dst_partner_id

    @api.multi
    def merge_cb(self):
        if self.change_account_invoice_and_move:
            self.action_change_account_invoice_and_move()
        return super(BasePartnerMergeAutomaticWizard, self).merge_cb()
