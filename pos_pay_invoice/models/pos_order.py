# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from openerp import models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def capute_invoice(self, invoice_id):
        inv = self.env['account.invoice'].browse(invoice_id)
        self.write({
            'partner_id': inv.partner_id,
        })

        self.env['pos.order.line'].create({
            'order_id': self.id,
            'product_id': '????',
            'qty': 1,
            'price_unit': inv.amount_total,
        })
