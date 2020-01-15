# Copyright 2019 Vicent Cubells - Trey <http://www.trey.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _prepare_invoice_line_from_po_line(self, line):
        vals = super()._prepare_invoice_line_from_po_line(line)
        vals['multiple_discount'] = line.multiple_discount
        vals['discount_name'] = line.discount_name
        return vals
