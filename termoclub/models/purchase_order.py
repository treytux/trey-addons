###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import xml.etree.cElementTree as et

from odoo import _, api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    termoclub_order_number = fields.Char(
        string='Order number',
        copy=False,
    )
    is_termoclub_order = fields.Boolean(
        string='Is TermoClub order',
        compute='_compute_is_termoclub_order',
    )
    termoclub_order_sent_type = fields.Selection(
        related='company_id.termoclub_order_sent_type'
    )
    termoclub_sent_state = fields.Selection(
        string='Sent state',
        selection=[
            ('no_sent', 'No sent'),
            ('sent', 'Sent'),
        ],
        default='no_sent',
    )

    @api.depends('partner_id')
    def _compute_is_termoclub_order(self):
        termoclub_supplier_id = self.env.user.company_id.termoclub_supplier_id
        for order in self:
            if termoclub_supplier_id == order.partner_id:
                order.is_termoclub_order = True

    def action_sent_to_termoclub(self):
        for order in self:
            if not order.is_termoclub_order:
                return False
            lines = order.mapped('order_line').filtered(
                lambda l: l.product_id.is_termoclub is True)
            if not lines:
                return False
            xml_order = {
                'PEDIDO': order.name,
                'OBSERV': order.notes and order.notes[:30] or '',
                'TIPENT': 'D',
                'DIRENV':
                    order.picking_type_id.warehouse_id.termoclub_address_id,
                'REFER': 'P',
            }
            for line in lines:
                cod_art = (line.product_id.seller_ids
                           and line.product_id.seller_ids[0].product_code)
                xml_order.update({
                    'DOCLIN_%s' % line.id: {
                        'CODART': cod_art,
                        'UNIDAD': line.product_qty,
                        'TPRES': 0,
                    }
                })
            termoclub = self.env.user.company_id.termoclub_client()
            client = termoclub.connection()
            res = termoclub.put_order(client=client, order=xml_order)
            msg = ''
            if res.find('R1') and res.find('R1').text is not None:
                if res.find('R2') is not None:
                    msg += _('<b>Send order error</b><p><ul><li><b>ID:</b> '
                             'Estructure:</li><li><b>Message:</b></li> '
                             '%s</ul>') % res.find('R2').text
                if res.find('R4') is not None:
                    msg += _('<b>Send order error</b><p><ul><li><b>ID:</b> '
                             'Import:</li><li><b>Message:</b></li> '
                             '%s</ul>') % res.find('R4').text
                if res.find('R3') is not None:
                    order.termoclub_order_number = res.find('R3').text
                    order.termoclub_sent_state = 'sent'
                    msg += _(
                        '<b>Purchase order has been sent</b><p><ul><li><b> '
                        'Order: </b> %s</li> <li><b>Message:</b></li> '
                        '%s</ul>') % (res.find('R3').text, res.find('R1').text)
            else:
                msg += _(
                    '<b>Send order error</b><p><ul><li><b>Message:</b></li> '
                    '%s</ul>') % (et.tostring(res, method='html'))
            self.message_post(body=msg)
