###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import models

_log = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _action_assign_cron(self):
        pickings = self.search([
            ('state', 'in', ['confirmed', 'waiting']),
        ], order='date')
        for index, picking in enumerate(pickings):
            try:
                _log.info('>>> Executing stock picking action assign cron...')
                with self.env.cr.savepoint():
                    if picking.state == 'confirmed':
                        picking.action_assign()
                        _log.info('[%s/%s] Assign confirmed picking %s' % (
                            index + 1, len(pickings), picking.name))
            except Exception as error:
                _log.error(
                    'Error in picking %s: %s' % (picking.name, error))
