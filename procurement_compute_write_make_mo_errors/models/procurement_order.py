# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _
import logging
_log = logging.getLogger(__name__)


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def make_mo(self):
        try:
            return super(ProcurementOrder, self.with_context(
                company_id=self.company_id.id)).make_mo()
        except Exception as e:
            msg = _(
                'Procurement order (id: %s): error on \'make_mo\' function: '
                '%s') % (self.id, e)
            _log.error(msg)
            self.message_post(body=msg)
            self.state = 'exception'
            return {self.id: None}
