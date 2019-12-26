# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _
import logging
_log = logging.getLogger(__name__)


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def _create_service_task(self, procurement):
        try:
            return super(ProcurementOrder, self.with_context(
                company_id=self.company_id.id))._create_service_task(
                    procurement)
        except Exception as e:
            msg = _(
                'Procurement order (id: %s): error on \'_create_service_task\''
                ' function: %s') % (procurement.id, e)
            _log.error(msg)
            procurement.message_post(body=msg)
            procurement.state = 'exception'
            return {procurement.id: None}
