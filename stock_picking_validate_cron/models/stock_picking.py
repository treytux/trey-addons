###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def cron_picking_validate(self, domain=None, days=None):
        if not domain or not days:
            raise ValidationError(
                _('Error validating arguments in the function call: '
                  'One or both parameters are not in the function call.'
                  'Both parameters are required in the function call.'))
        if not isinstance(domain, list):
            raise ValidationError(
                _('Error validating the domain: The domain has to be a list'))
        for condition in domain:
            if 'state' in condition:
                raise ValidationError(
                    _('Error validating the domain: State cannot be passed in'
                      ' the domain'))
        limit_date = datetime.now() + relativedelta(days=int(days))
        domain += [
            ('state', '=', 'assigned'),
            ('scheduled_date', '<', limit_date.strftime('%Y-%m-%d')),
        ]
        pickings = self.env['stock.picking'].search(domain)
        for picking in pickings:
            reserved_qty = sum(
                picking.move_ids_without_package.mapped(
                    'reserved_availability'))
            product_qty = sum(
                picking.move_ids_without_package.mapped('product_uom_qty'))
            if reserved_qty == product_qty:
                for move in picking.move_lines:
                    move.quantity_done = move.product_uom_qty
                picking.action_done()
