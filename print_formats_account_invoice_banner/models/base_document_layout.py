###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    invoice_banner = fields.Html(
        related='company_id.invoice_banner',
        readonly=False,
    )
