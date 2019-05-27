# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def onchange_partner_id(self, part):
        partner = self.env['res.partner'].browse(part)
        if partner.credit_total < 0 and partner.block_when_unpaid:
            partner.sale_warn = 'block'
            partner.sale_warn_msg = '%s, %s' % (
                _('This partner is blocked for unpaid.'),
                partner.sale_warn_msg and partner.sale_warn_msg or '')
        return super(SaleOrder, self).onchange_partner_id(part)
