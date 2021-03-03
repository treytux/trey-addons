###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields, models

_log = logging.getLogger(__name__)


class AccountInvoiceEdeLogLine(models.Model):
    _name = 'account.invoice.ede.log.line'
    _description = 'Ede invoice process log line'
    _rec_name = 'ede_invoice_number'

    log_id = fields.Many2one(
        comodel_name='account.invoice.ede.log',
        string='Log',
        required=True,
        ondelete='cascade',
        index=True,
    )
    ede_date_invoice = fields.Date(
        string='Date invoice',
    )
    ede_invoice_number = fields.Char(
        string='Invoice',
        required=True,
    )
    ede_xml_name = fields.Char(
        string='File name',
        required=True,
    )
    ede_xml_data = fields.Text(
        string='XML',
        required=True,
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
    supplier_invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Supplier invoice',
    )
