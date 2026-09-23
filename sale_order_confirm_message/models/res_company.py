###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    sale_confirm_message_active = fields.Boolean(
        string='Review dialog on quotation confirm',
        default=True,
        help='Show a dialog with the key data to review against the '
             'customer-signed document before confirming a quotation.',
    )
    sale_confirm_message_require_check = fields.Boolean(
        string='Require explicit review check',
        default=True,
        help='The salesperson must tick a checkbox stating that the data '
             'has been reviewed before the quotation can be confirmed.',
    )
    sale_confirm_message_body = fields.Text(
        string='Quotation confirmation message',
        translate=True,
        default=lambda self: self._default_sale_confirm_message_body(),
    )

    def _default_sale_confirm_message_body(self):
        return _(
            'Please check the important information against the document '
            'signed by the customer. Once confirmed, the following data '
            'cannot be modified:')
