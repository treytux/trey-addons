# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class StockTransferDetailsItems(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    @api.multi
    def split_quantities_completely(self):
        for transfer_detail in self:
            for q in range(1, int(transfer_detail.quantity)):
                transfer_detail.copy({'quantity': 1, 'packop_id': False})
            transfer_detail.quantity = 1
        return self[0].transfer_id.wizard_view()
