# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def onchange_partner_id(self, part=False):
        res = super(PosOrder, self).onchange_partner_id(part=part) or {}
        if not part:
            return res

        def _message_parent(partner):
            if partner and partner.sale_warn != 'no-message':
                title = _('Warning for %s') % partner.name
                message = partner.sale_warn_msg
                if partner.sale_warn == 'block':
                    raise exceptions.Warning(title, message)
                return {'warning': {'title': title, 'message': message}}
            if partner.parent_id:
                return _message_parent(partner.parent_id)
            return {}

        partner = self.env['res.partner'].browse(part)
        res.update(_message_parent(partner))
        return res

    @api.multi
    def action_invoice(self):
        self.ensure_one()
        res = self.env['account.invoice'].onchange_partner_id(
            'out_invoice', self.partner_id.id)
        if 'warning' in res and self.partner_id.invoice_warn == 'block':
            w = res['warning']
            raise exceptions.Warning(w['title'], w['message'])
        return super(PosOrder, self).action_invoice()
