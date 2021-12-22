###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import _, api, models

_log = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def send_mail_line_from_orderpoint(self, mail_server, line):
        email_from = mail_server.smtp_user
        email_to = ', '.join(
            [u.login for u in line.company_id.users_to_send_mail_ids])
        msg = _(
            'Purchase order line created form orderpoint:\n'
            '\t- Product: %s'
            '\t- Quantity: %s'
            '\t- Purchase order: %s') % (
                line.product_id.display_name, line.product_uom_qty,
                line.order_id.name)
        mail = self.env['mail.mail'].create({
            'subject': _('Purchase order line created form orderpoint'),
            'email_from': email_from,
            'email_to': email_to,
            'body_html': msg,
        })
        mail.send()

    def check_from_orderpoint_and_send_mail(self):
        mail_server = self.env['ir.mail_server'].search([])
        if not mail_server:
            _log.error((
                'No outgoing mail server found on the system; mails cannot be '
                'sent.'))
            return
        op_sequence = self.env.ref('stock.sequence_mrp_op')
        for line in self:
            purchase_origin = line.order_id.origin
            if purchase_origin and op_sequence.prefix in purchase_origin:
                self.send_mail_line_from_orderpoint(mail_server, line)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.check_from_orderpoint_and_send_mail()
        return res
