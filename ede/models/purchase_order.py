# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import datetime
import logging
from openerp import fields, models, api, exceptions, _
from openerp.osv import expression
from ..tools import utilities

_log = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    ede_order_number = fields.Char(
        string='EDE Order Number',
        copy=False
    )
    ede_document_id = fields.Char(
        string='EDE Document Id',
        copy=False
    )
    ede_state = fields.Selection(
        string='EDE State',
        selection=[
            ('A', 'Open'),
            ('B', 'A part has been delivered '),
            ('C', 'Finish'),
        ],
        track_visibility='onchange',
        copy=False,
    )
    ede_tracking_msg = fields.Char(
        string='Tracking Message',
        copy=False,
    )
    ede_shipping = fields.Selection(
        string='EDE Shipping',
        selection=[('10', 'UPS Standard'),
                   ('11', 'UPS Express 9:00 a.m'),
                   ('12', 'UPS Express 10:30 a.m'),
                   ('13', 'UPS Express by 12:00 a.m'),
                   ('20', 'Express delivery by forwarding agency'),
                   ('30', 'Standard Shipping')],
        default='13',
        copy=False,
    )
    ede_send_type = fields.Selection(
        string='EDE Order Type',
        selection=[
            ('0', "Partials Delivery's"),
            ('1', "Send Complete")
        ],
        default='0',
        copy=False,
    )
    is_ede_order = fields.Boolean(
        string='EDE Order',
        compute='_is_ede_order',
    )
    is_ede_send = fields.Boolean(
        string='EDE Send',
        copy=False
    )
    ede_client_order_ref = fields.Char(
        string='Client Ref',
    )
    customer_shipping_id = fields.Many2one(
        comodel_name='res.partner',
        string='Delivery Address'
    )
    is_ede_danger = fields.Boolean(
        string='EDE Danger',
        copy=False
    )
    is_ede_custom = fields.Boolean(
        string='EDE Custom Route',
    )
    ede_date_delivered = fields.Datetime(
        string='Date Delivered',
    )
    ede_signed_name = fields.Char(
        string='Signed Name',
    )
    adarra_ede_state = fields.Selection(
        string='EDE / Adarra State',
        selection=[
            ('draft', 'Draft'),
            ('simulated', 'Simulated'),
            ('send', 'Send'),
            ('purchase', 'Purchase Received'),
            ('sale', 'Sale Received'),
            ('email', 'Email Sent'),
            ('done', 'Done'),
        ],
        default='draft',
        copy=False,
        track_visibility='onchange',
    )

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        make_po_normal_conditions = {
            'partner_id', 'state', 'picking_type_id', 'location_id',
            'company_id', 'dest_address_id'}
        if make_po_normal_conditions.issubset(set(x[0] for x in args)):
            args = expression.normalize_domain(args)
            args = expression.AND((args, [('is_ede_custom', '=', False)]))
        return super(PurchaseOrder, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    @api.depends('order_line.is_ede_danger')
    @api.one
    def _is_ede_danger(self):
        lines = self.mapped(
            'lines').filtered(lambda l: l.is_ede_danger is True)
        if lines:
            self.is_ede_order = True

    @api.depends('partner_id')
    @api.one
    def _is_ede_order(self):
        if self.company_id.ede_supplier_id.id == self.partner_id.id:
            self.is_ede_order = True

    @api.one
    def action_send_to_ede(self):
        if self.is_ede_send:
            raise exceptions.Warning(_("Purchase Order it's Already Send "))
        not_ean = self.mapped('order_line').filtered((
            lambda l: l.product_id.ean13 is None))
        if not_ean:
            raise exceptions.Warning(
                _('Products Without EAN code ' % not_ean[0].product_id.name))
        items = []
        for line in self.order_line:
            items.append({
                'ID': line.id,
                'ProductID': line.product_id.ean13,
                'Quantity': line.product_qty,
            })
        recipient = {}
        if self.customer_shipping_id:
            if self.customer_shipping_id.parent_id:
                name_1 = self.customer_shipping_id.parent_name
                name_2 = self.customer_shipping_id.name
            else:
                name_1 = self.customer_shipping_id.name
                name_2 = self.customer_shipping_id.name
            address = {
                'type': 'EK',
                'AddressID': self.customer_shipping_id.id,
                'Name1': name_1,
                'Name2': name_2,
                'Street': '%s %s' % (
                    self.customer_shipping_id.street,
                    self.customer_shipping_id.street2),
                'ZipCode': self.customer_shipping_id.zip,
                'City': '%s %s' % (
                    self.customer_shipping_id.city,
                    self.customer_shipping_id.state_id and
                    self.customer_shipping_id.state_id.name or ''),
                'CountryCode':
                    self.customer_shipping_id.country_id and
                    self.customer_shipping_id.country_id.code or 'ES'
            }
            recipient['Address'] = address
        payload = {
            'ShipmentTypeCode': self.ede_shipping,
            'DeliveryComplete': self.ede_send_type,
            'OrderMemberID': self.name,
            'OrderMemberCustomerID':
                self.ede_client_order_ref or self.origin or '',
            'Department': 'Purchase',
            'CommissionID': '',
            'Remark': self.notes or self.ede_client_order_ref or '',
            'Recipient': recipient,
            'Items': {'Item': items},
        }
        ede = self.company_id.ede_client()
        client = ede.connection()
        credentials = self.company_id.ede_credentials()
        ede_order = ede.create_order(
            client=client, credentials=credentials, payload=payload)
        response = ede_order.findall(
            ".//SalesOrderCreateConfirmation/Protocol/Item")
        if not response:
            msg = _('Error Send Purchase Order<p><ul><li><b>Message: '
                    'Connection response Error</b>')
            self.message_post(body=msg)
            return
        if response[0].find('Severity').text != 'S':
            msg = _('Error Send Purchase Order<p><ul><li><b>ID:</b> %s</li>'
                    '<li><b>Message:</b> %s</li></ul>') % (
                response[0].find('ID').text, response[0].find('Text').text)
            self.message_post(body=msg)
            return
        self.write({
            'ede_document_id': response and response[0].find('ID').text,
            'is_ede_send': True,
            'ede_state': 'A',
            'adarra_ede_state': 'send'
        })
        msg = _('Purchase Order is Send <p><ul><li><b>ID:</b> %s</li>'
                '<li><b>Message:</b></li> %s</ul>') % (
            response[0].find('ID').text, response[0].find('Text').text)
        self.message_post(body=msg)
        if self.origin:
            origin = self.origin.split(':')[0]
            sale_order = self.env['sale.order'].search(
                [('name', '=', origin)], limit=1)
            if sale_order:
                sale_order.write({'adarra_ede_state': 'send'})

    @api.multi
    def ede_check_status(self, orders):
        ede = orders[0].company_id.ede_client()
        _log.info('=' * 75)
        for order in orders:
            _log.info('Processing Purchase Order: %s' % order.name)
            res = ede.get_order_status(order_id=order.ede_document_id)
            if res.find('DocNumber').text != order.ede_document_id:
                continue
            if res.find('Status').text == 'A':
                continue
            activities = res.findall('.//Trackitem/Activities/Activity')
            if not activities:
                continue
            status = activities[0].findall('Status')
            if status[0].find('Type').text != 'D':
                continue
            location = activities[0].findall('Location')
            delivered_signed = location[0].find('SignedForByName').text
            date_format = '%Y%m%d %H%M%S'
            date_time_str = '%s %s' % (
                activities[0].find('Date').text,
                activities[0].find('Time').text
            )
            delivered_datetime = datetime.datetime.strptime(
                date_time_str, date_format).strftime(date_format)
            order.write({
                'ede_date_delivered': delivered_datetime,
                'ede_signed_name': delivered_signed
            })
            items = res.findall('.//Itemlist/Item')
            lines = []
            for item in items:
                if item.find('StatusCode').text == 'A':
                    continue
                ean_13 = utilities.sanitize_ean13(item.find('ProductID').text)
                purchase_line = order.mapped('order_line').filtered(
                    lambda l: l.product_id.ean13 == ean_13)
                if not purchase_line:
                    continue
                ede_invoice = item.findall('DocumentsInvoice')
                if not ede_invoice:
                    continue
                if not order.customer_shipping_id:
                    order.ede_status = res.find('Status').text
                    continue
                purchase_line.write({
                    'ede_invoice_id': ede_invoice[0].find('DocumentID').text
                })
                ede_data = {
                    'purchase_line': purchase_line,
                    'item': item,
                }
                for tracking in res.findall('.//Tracklist/Item'):
                    if tracking.find(
                            'ItemNumber').text == item.find('ItemNumber').text:
                        ede_data['tracking'] = tracking
                lines.append(ede_data)
            if not order.customer_shipping_id:
                _log.info('=' * 75)
                continue
            _log.info('Process Confirm Purchase: %s Pickings' % order.name)
            to_confirm_sale = self.ede_confirm_purchase_order(order, lines)
            _log.info('Process Confirm Sales Picking')
            if not to_confirm_sale:
                _log.info(
                    'Not Sales Picking to confirm Purchase: %s' % order.name)
                _log.info('=' * 75)
                continue
            send_email = self.ede_confirm_sale_order(order, lines)
            if not send_email:
                _log.info(
                    'Not Sales Picking to Send Email Purchase: %s' %
                    order.name)
                _log.info('=' * 75)
                continue
            to_purchase_change_state = self.ede_picking_send_email(send_email)
            if not to_purchase_change_state:
                continue
            order.ede_state = res.find('Status').text
        return True

    @api.multi
    def ede_confirm_purchase_order(self, order=None, lines=None):
        pickings = order.mapped('picking_ids').filtered(
            lambda p:
            p.state in ('assigned', 'partially_available') and
            p.picking_type_code == 'incoming')
        if not pickings:
            return False
        for picking in pickings:
            for line in lines:
                qty_delivered = float(line['item'].find('QuantityDlv').text)
                if qty_delivered == 0.00:
                    continue
                move = picking.mapped('move_lines').filtered(
                    lambda m: m.product_id.id == line[
                        'purchase_line'].product_id.id)
                if not move:
                    continue
                pack_data = {
                    'product_id': line['purchase_line'].product_id.id,
                    'product_uom_id': line['purchase_line'].product_uom.id,
                    'product_qty': qty_delivered,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'date': move.date if move.date else datetime.now(),
                    'owner_id': self.env.user.id,
                    'picking_id': picking.id,
                }
                self.env['stock.pack.operation'].create(pack_data)
            comment = _('Delivered date: %s Signed by: %s' % (
                order.ede_date_delivered, order.ede_signed_name))
            picking.write({
                'client_reference': order.ede_client_order_ref,
                'purchase_comment': comment,
            })
            picking.do_transfer()
            _log.info('Confirmed Picking to Purchase: %s' % order.name)
            order.write({'adarra_ede_state': 'purchase'})
            if order.origin:
                origin = order.origin.split(':')[0]
                sale_order = self.env['sale.order'].search(
                    [('name', '=', origin)])
                if sale_order:
                    sale_order.write({'adarra_ede_state': 'purchase'})
        self.env.cr.commit()
        return True

    @api.multi
    def ede_confirm_sale_order(self, order=None, lines=None):
        picking_to_send_email = []
        if not order.origin:
            if order.customer_shipping_id and order.ede_client_order_ref:
                msg = _(
                    'Purchase order confirmed without associated sales order')
                order.message_post(body=msg)
                order.ede_state = 'C'
                order.adarra_ede_state = 'done'
                self.env.cr.commit()
                return False
        origin = order.origin.split(':')[0]
        customer_route = self.env['stock.location.route'].search([
            ('is_sale_one_purchase', '=', True),
            ('is_drop_shipping', '=', True)])
        sale_order = self.env['sale.order'].search([
            ('partner_shipping_id', '=', order.customer_shipping_id.id),
            ('name', '=', origin)])
        if not sale_order:
            return False
        if len(sale_order) > 1:
            _log.info('Several sales orders found for this purchase order')
        pickings = sale_order.mapped('picking_ids').filtered(
            lambda p:
            p.state in ('assigned', 'partially_available', 'waiting') and
            p.picking_type_code == 'outgoing')
        if not pickings:
            return False
        for picking in pickings:
            moves = self.env['stock.move'].search([
                ('picking_id', '=', picking.id),
                ('route_ids', 'in', customer_route.id)])
            if not moves:
                return False
            for move in moves:
                for line in lines:
                    if not line['purchase_line'].product_id == move.product_id:
                        continue
                    else:
                        qty_delivered = float(
                            line['item'].find('QuantityDlv').text)
                        pack_data = {
                            'product_id': line['purchase_line'].product_id.id,
                            'product_uom_id': line[
                                'purchase_line'].product_uom.id,
                            'product_qty': qty_delivered,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'date': move.date if move.date else datetime.now(),
                            'owner_id': self.env.user.id,
                            'picking_id': picking.id,
                        }
                        self.env['stock.pack.operation'].create(pack_data)
            comment = _('Delivered date: %s Signed by: %s' % (
                order.ede_date_delivered, order.ede_signed_name))
            picking.write({
                'client_reference': order.ede_client_order_ref or '',
                'sale_comment': comment,
            })
            picking.do_transfer()
            picking_to_send_email.append({
                'picking': picking,
                'purchase': order,
                'sale': sale_order
            })
            _log.info(
                'Confirmed Picking: %s from Sale: %s and Purchase: %s' % (
                    picking.name, sale_order.name, order.name))
        if sale_order:
            sale_order.write({'adarra_ede_state': 'sale'})
        order.write({'adarra_ede_state': 'sale'})
        self.env.cr.commit()
        return picking_to_send_email

    @api.multi
    def ede_picking_send_email(self, data):
        if not data[0].get('sale') and not data[0].get('picking'):
            return False
        sale_order = data[0].get('sale')
        purchase_order = data[0].get('purchase')
        picking = data[0].get('picking')
        ctx = self.env.context.copy()
        ctx['is_ede_send'] = True
        ede_user = \
            self.env.user.company_id and \
            self.env.user.company_id.ede_user_id or None
        ctx['user_id'] = ede_user or self.env.user
        ctx['mail_post_autofollow'] = True
        try:
            template = self.env.ref(
                'stock_picking_send_by_mail.email_template_stock_picking')
            template.with_context(ctx).send_mail(picking.id, force_send=True)
        except Exception:
            _log.info('ERROR Send Email from Picking:%s and Sale:%s' % (
                picking.name, sale_order.name))
            self.env.cr.commit()
            return False
        _log.info('Send Email from Picking:%s and Sale:%s' % (
            picking.name, sale_order.name))
        sale_order.write({
            'adarra_ede_state': 'done',
        })
        purchase_order.write({
            'adarra_ede_state': 'done',
        })
        self.env.cr.commit()
        return True

    @api.model
    def _run_ede_check_status(self):
        orders = self.env['purchase.order'].search([
            ('state', 'not in', ('done', 'cancel')),
            ('is_ede_send', '=', True), ('ede_state', '!=', 'C')],
            order='date_order desc')
        if not orders:
            return False
        self.ede_check_status(orders)
