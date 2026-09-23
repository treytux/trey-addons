###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    supplier_invoice_number = fields.Char(
        string='Supplier invoice number',
        copy=False,
    )
    supplier_invoice_date = fields.Date(
        string='Supplier invoice date',
        copy=False,
    )
    supplier_invoice_file = fields.Binary(
        string='Supplier invoice file',
        copy=False,
    )
