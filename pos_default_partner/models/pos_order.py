# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def get_partner_from_session_id(self, session_id):
        session = self.env['pos.session'].browse(session_id)
        if session.config_id.default_partner_id:
            return session.config_id.default_partner_id.id
        return False

    @api.model
    def default_get(self, fields):
        res = super(PosOrder, self).default_get(fields)
        if 'session_id' not in res or 'partner_id' in res:
            return res
        res['partner_id'] = self.get_partner_from_session_id(res['session_id'])
        return res

    @api.model
    def create_from_ui(self, orders):
        for data in orders:
            order = data['data']
            if not order.get('partner_id'):
                order['partner_id'] = self.get_partner_from_session_id(
                    order['pos_session_id'])
        return super(PosOrder, self).create_from_ui(orders=orders)
