# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    subvention_percent = fields.Float(
        string='Subvention (%)')
    subvention_id = fields.Many2one(
        comodel_name='account.subvention',
        string='Subvention')

    @api.multi
    def product_id_change(
        self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False,
            currency_id=False, company_id=None):
        res = super(AccountInvoiceLine, self).product_id_change(
            product, uom_id, qty=qty, name=name, type=type,
            partner_id=partner_id, fposition_id=fposition_id,
            price_unit=price_unit, currency_id=currency_id,
            company_id=company_id)
        res['value'].update({
            'subvention_percent': 0.0,
            'subvention_id': None})
        if not product:
            return res
        product = self.env['product.product'].browse(product)
        if not product.subvention_ok:
            return res
        partner = self.env['res.partner'].browse(partner_id)
        res['value'].update({
            'subvention_percent': (
                partner.subvention_id and partner.subvention_percent or 0.0),
            'subvention_id': (
                partner.subvention_id and partner.subvention_id.id or None)})
        return res

    @api.model
    def move_line_get_item(self, line):
        res = super(AccountInvoiceLine, self).move_line_get_item(line)
        res['subvention_id'] = (
            line.subvention_id and line.subvention_id.id or None)
        res['subvention_percent'] = line.subvention_percent
        return res
