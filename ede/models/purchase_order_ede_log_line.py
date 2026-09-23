###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields, models

_log = logging.getLogger(__name__)


class PurchaseOrderEdeLogLine(models.Model):
    _name = 'purchase.order.ede.log.line'
    _description = 'Ede purchase order process log line'
    _rec_name = 'ede_purchase_order_number'
    _order = 'create_date desc'

    log_id = fields.Many2one(
        comodel_name='purchase.order.ede.log',
        string='Log',
        required=True,
        ondelete='cascade',
        index=True,
    )
    ede_date_purchase_order = fields.Date(
        string='Date purchase order',
    )
    ede_purchase_order_number = fields.Char(
        string='Purchase order',
    )
    state = fields.Selection(
        selection=[
            ('fail', 'Fail'),
            ('warning', 'Warning'),
            ('done', 'Done'),
        ],
        string='State',
        default='done',
        required=True,
    )
    log = fields.Text(
        string='Log description',
    )
    supplier_purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Supplier purchase order',
    )
