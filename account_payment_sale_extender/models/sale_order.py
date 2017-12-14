# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    customer_partner_bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string=u'Customer Bank Account',
        domain="[('partner_id', '=', partner_id)]",
        help="Select the bank account of your customer on which your company "
             "should send the payment. This field is copied from the partner "
             "and will be copied to the customer invoice."
    )

    @api.model
    def _get_default_customer_partner_bank(self, partner):
        """This function is designed to be inherited"""
        return partner.bank_ids and partner.bank_ids[0].id or False

    @api.multi
    def onchange_partner_id(self, partner_id):
        res = super(SaleOrder, self).onchange_partner_id(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            res['value']['customer_partner_bank_id'] = \
                self._get_default_customer_partner_bank(partner)
            res['value']['payment_mode_id'] = partner.customer_payment_mode.id
        else:
            res['value']['payment_mode_id'] = False
            res['value']['customer_partner_bank_id'] = False
        return res

    @api.model
    def _prepare_invoice(self, order, lines):
        """Copy bank partner from sale order to invoice"""
        vals = super(SaleOrder, self)._prepare_invoice(order, lines)
        if order.payment_mode_id:
            vals['payment_mode_id'] = order.payment_mode_id.id,
            vals['partner_bank_id'] = order.customer_partner_bank_id.id
        return vals
