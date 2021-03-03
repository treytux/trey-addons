###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime
import logging

from odoo import SUPERUSER_ID, _, api, exceptions, fields, models

_log = logging.getLogger(__name__)


def migrate_sale_order_id(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    purchases = env['purchase.order'].search([
        ('ede_workflow_state', 'not in', ('done', 'draft')),
        ('ede_state', '!=', 'C')])
    for purchase in purchases:
        if not purchase.origin:
            continue
        origin = purchase.origin.split(':')[0]
        sale_order = env['sale.order'].search([('name', '=', origin)], limit=1)
        if sale_order:
            purchase.sudo().write({'sale_order_id': sale_order.id})


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    ede_order_number = fields.Char(
        string='EDE Order Number',
        copy=False,
    )
    ede_document_id = fields.Char(
        string='EDE Document Id',
        copy=False,
    )
    ede_state = fields.Selection(
        string='EDE State',
        selection=[
            ('A', 'Open'),
            ('B', 'A part has been delivered'),
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
        selection=[
            ('10', 'UPS Standard'),
            ('11', 'UPS Express 9:00 a.m'),
            ('12', 'UPS Express 10:30 a.m'),
            ('13', 'UPS Express by 12:00 a.m'),
            ('20', 'Express delivery by forwarding agency'),
            ('30', 'Standard Shipping')
        ],
        default='13',
        copy=False,
    )
    ede_send_type = fields.Selection(
        string='EDE Order Type',
        selection=[
            ('0', 'Partials Delivery\'s'),
            ('1', 'Send Complete'),
        ],
        default='0',
        copy=False,
    )
    is_ede_order = fields.Boolean(
        string='EDE Order',
        compute='_compute_is_ede_order',
    )
    is_ede_send = fields.Boolean(
        string='EDE Send',
        copy=False,
    )
    ede_client_order_ref = fields.Char(
        string='Client Ref',
    )
    customer_shipping_id = fields.Many2one(
        comodel_name='res.partner',
        string='Delivery Address',
    )
    is_ede_danger = fields.Boolean(
        string='EDE Danger',
        copy=False,
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
    ede_workflow_state = fields.Selection(
        string='EDE / Workflow State',
        old_name='adarra_ede_state',
        selection=[
            ('draft', 'Draft'),
            ('simulated', 'Simulated'),
            ('send', 'Send'),
            ('purchase', 'Purchase Received'),
            ('sale', 'Sale Received'),
            ('email', 'Email Pending'),
            ('done', 'Done'),
        ],
        default='draft',
        copy=False,
        track_visibility='onchange',
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
    )

    @api.depends('order_line.is_ede_danger')
    def _compute_is_ede_danger(self):
        for order in self:
            lines = order.mapped('lines').filtered(
                lambda l: l.is_ede_danger is True)
            order.is_ede_order = bool(lines)

    @api.depends('partner_id')
    def _compute_is_ede_order(self):
        for order in self:
            if self.env.user.company_id.ede_supplier_id == order.partner_id:
                order.is_ede_order = True

    def action_send_to_ede(self):
        for order in self:
            if order.is_ede_send:
                raise exceptions.Warning(_(
                    'Purchase Order it\'s Already Send.'))
            not_ean = order.mapped('order_line.product_id').filtered(
                lambda p: not p.barcode)
            if not_ean:
                product_names = '\n'.join(not_ean.mapped('name'))
                raise exceptions.Warning(_(
                    'Products Without barcode:\n%s ' % product_names))
            items = []
            for line in self.order_line:
                items.append({
                    'ID': line.id,
                    'ProductID': line.product_id.barcode,
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
                        self.customer_shipping_id.street2,
                    ),
                    'ZipCode': self.customer_shipping_id.zip,
                    'City': '%s %s' % (
                        self.customer_shipping_id.city,
                        self.customer_shipping_id.state_id
                        and self.customer_shipping_id.state_id.name or ''),
                    'CountryCode': (
                        self.customer_shipping_id.country_id
                        and self.customer_shipping_id.country_id.code or 'ES')
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
            client = ede.wsd_connection()
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
                msg = _(
                    'Error Send Purchase Order<p><ul><li><b>ID:</b> %s</li>'
                    '<li><b>Message:</b> %s</li></ul>') % (
                    response[0].find('ID').text, response[0].find('Text').text)
                self.message_post(body=msg)
                return
            self.write({
                'ede_document_id': response and response[0].find('ID').text,
                'is_ede_send': True,
                'ede_state': 'A',
                'ede_workflow_state': 'send'
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
                    sale_order.write({'ede_workflow_state': 'send'})

    @api.multi
    def ede_check_status(self, orders):
        ede = orders[0].company_id.ede_client()
        for order in orders:
            if not order.sale_order_id:
                continue
            start_code = order.company_id.ede_start_code
            if order.ede_workflow_state in ('email', 'done'):
                order.ede_state = 'C'
                continue
            check_products = False
            _log.info('Processing Purchase Order: %s' % order.name)
            res = ede.get_order_status(order_id=order.ede_document_id)
            if not res:
                continue
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
                msg_item = ''
                if item.find('StatusCode').text == 'A':
                    continue
                ean_13 = self.env['barcode.nomenclature'].sanitize_ean(
                    item.find('ProductID').text)
                default_code = '%s%s' % (
                    start_code, item.find('ProductOriginID').text[2:])
                purchase_line = order.mapped('order_line').filtered(
                    lambda l: l.product_id.barcode == ean_13)
                if not purchase_line:
                    if len(default_code) < 12:
                        purchase_line = order.mapped('order_line').filtered(
                            lambda l: l.product_id.default_code == default_code
                        )
                    else:
                        msg_item = _(
                            'Purchase line no exist with EAN: %s with '
                            'description: %s' % (
                                ean_13, item.find('ShortText').text or ''))
                        check_products = True
                    order.message_post(body=msg_item)
                    continue
                if not purchase_line:
                    msg_item = _(
                        'Purchase line no exist with EAN: %s and Product '
                        'code: %s and description: %s' % (
                            ean_13, default_code, item.find(
                                'ShortText').text or ''))
                    order.message_post(body=msg_item)
                    check_products = True
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
                sale_line = order.sale_order_id.mapped(
                    'order_line').filtered(
                    lambda l: l.product_id == purchase_line.product_id)
                ede_data['sale_line'] = sale_line or None
                for tracking in res.findall('.//Tracklist/Item'):
                    if tracking.find(
                            'ItemNumber').text == item.find('ItemNumber').text:
                        ede_data['tracking'] = tracking
                lines.append(ede_data)
            if check_products:
                _log.info('Fail Purchase Order: %s Error: products invalid' %
                          order.name)
                continue
            if not order.customer_shipping_id:
                _log.info('Fail Purchase Order: %s Error: Not Customer '
                          'Shipping Address' % order.name)
                continue
            _log.info('Process Confirm Purchase: %s Pickings' % order.name)
            to_confirm_sale = self.ede_confirm_purchase_order(order, lines)
            _log.info('Process Confirm Sales Picking')
            if not to_confirm_sale:
                _log.info(
                    'Not Sales Picking to confirm Purchase: %s' % order.name)
                continue
            send_email = self.ede_confirm_sale_order(order, lines)
            if not send_email:
                _log.info(
                    'Not Sales Picking to Send Email Purchase: %s' %
                    order.name)
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
            (p.state in ('assigned', 'partially_available', 'waiting')
             and p.picking_type_code == 'incoming'))
        if not pickings:
            return bool(order.ede_workflow_state != 'purchase')
        for picking in pickings:
            process_picking = False
            for line in lines:
                qty_delivered = float(line['item'].find('QuantityDlv').text)
                if qty_delivered == 0.00:
                    continue
                move = picking.mapped('move_ids_without_package').filtered(
                    lambda m: m.purchase_line_id.id == line[
                        'purchase_line'].id)
                if not move:
                    continue
                if len(move) > 1:
                    move = move[0]
                if move.state != 'assigned':
                    continue
                move.move_line_ids.write({'qty_done': qty_delivered})
                process_picking = True
            comment = _('Customer ref: %s Delivered date: %s Signed by: %s' % (
                order.ede_client_order_ref, order.ede_date_delivered,
                order.ede_signed_name))
            if not process_picking:
                continue
            picking.note = comment
            _log.info('Confirming Picking: %s to Purchase: %s' % (
                picking.name, order.name))
            picking.button_validate()
            picking.action_done()
            _log.info('Confirmed Picking: %s to Purchase: %s' % (
                picking.name, order.name))
            order.write({'ede_workflow_state': 'purchase'})
            order.sale_order_id.write({'ede_workflow_state': 'purchase'})
            self.env.cr.commit()
        return True

    @api.multi
    def ede_confirm_sale_order(self, order=None, lines=None):
        picking_to_send_email = []
        if not order.sale_order_id:
            if order.customer_shipping_id and order.ede_client_order_ref:
                msg = _('Purchase order confirmed without sales order')
                order.message_post(body=msg)
                order.ede_state = 'C'
                order.ede_workflow_state = 'done'
                return False
        pickings = order.sale_order_id.mapped('picking_ids').filtered(
            lambda p:
            p.state in (
                'assigned', 'partially_available', 'waiting', 'confirmed')
            and p.picking_type_code == 'outgoing')
        if not pickings and order.ede_workflow_state == 'sale':
            return True
        if not pickings:
            return False
        for picking in pickings:
            process_picking = False
            for line in lines:
                if not line.get('sale_line'):
                    continue
                move = picking.mapped('move_ids_without_package').filtered(
                    lambda p: p.sale_line_id.id == line['sale_line'].id)
                if not move:
                    continue
                if len(move) > 1:
                    move = move[0]
                qty_delivered = float(line['item'].find('QuantityDlv').text)
                move.move_line_ids.write({'qty_done': qty_delivered})
                process_picking = True
            if not process_picking:
                continue
            comment = _('Customer ref: %s Delivered date: %s Signed by: %s' % (
                order.ede_client_order_ref, order.ede_date_delivered,
                order.ede_signed_name))
            picking.note = comment
            _log.info(
                'Confirming Picking: %s from Sale: %s and Purchase: %s' % (
                    picking.name, order.sale_order_id.name, order.name))
            picking.button_validate()
            picking.action_done()
            picking_to_send_email.append({
                'picking': picking,
                'purchase': order,
            })
            _log.info(
                'Confirmed Picking: %s from Sale: %s and Purchase: %s' % (
                    picking.name, order.sale_order_id.name, order.name))
        order.sale_order_id.write({'ede_workflow_state': 'sale'})
        order.write({'ede_workflow_state': 'sale'})
        self.env.cr.commit()
        if not picking_to_send_email:
            return False
        return picking_to_send_email

    @api.multi
    def ede_picking_send_email(self, data):
        if type(data) == bool:
            return False
        if not data[0].get('picking'):
            return False
        if not data[0].get('purchase'):
            return False
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
            _log.info('ERROR Send Email from Picking: %s and Sale: %s' % (
                picking.name, purchase_order.sale_order_id.name))
            purchase_order.sale_order.write({
                'ede_workflow_state': 'email',
            })
            purchase_order.write({
                'ede_workflow_state': 'email',
            })
        _log.info('Send Email from Picking: %s and Sale: %s' % (
            picking.name, purchase_order.sale_order_id.name))
        purchase_order.sale_order_id.write({
            'ede_workflow_state': 'done',
        })
        purchase_order.write({
            'ede_workflow_state': 'done',
        })
        return True

    @api.model
    def _run_ede_check_status(self):
        orders = self.env['purchase.order'].search([
            ('state', 'not in', ('done', 'cancel')),
            ('is_ede_send', '=', True), ('ede_state', 'in', ('A', 'B')),
            ('sale_order_id', '!=', None)], order='date_order desc')
        if not orders:
            return False
        self.ede_check_status(orders)

    @api.multi
    def action_check_status(self):
        for order in self:
            self.ede_check_status(order)

    @api.multi
    def ede_ftp_invoice(self, orders=None):
        def data_header_info(xml=None):
            header = xml['INVOICE']['INVOICE_HEADER']
            data = {
                'invoice_id': header['INVOICE_INFO']['INVOICE_ID'],
                'invoice_date': fields.Date.from_string(
                    header['INVOICE_INFO']['INVOICE_DATE']),
                'supplier_order_id': header[
                    'ORDER_HISTORY']['SUPPLIER_ORDER_ID'],
            }
            if header['ORDER_HISTORY'].get('ORDER_ID'):
                data['order_id'] = header['ORDER_HISTORY']['ORDER_ID']
            return data

        def data_line_info(item=None):
            if not item.get('ORDER_REFERENCE'):
                return {}
            return {
                'item_customer_ref': item[
                    'ORDER_REFERENCE']['ORDER_ID'],
                'item_customer_id': int(
                    item['ORDER_REFERENCE']['LINE_ITEM_ID']),
                'item_order_ref': item[
                    'SUPPLIER_ORDER_REFERENCE']['SUPPLIER_ORDER_ID'].strip(),
                'item_quantity': float(item['QUANTITY']),
                'item_price_fix': float(
                    item['PRODUCT_PRICE_FIX']['bmecat:PRICE_AMOUNT']),
                'item_price_line_amount': float(item['PRICE_LINE_AMOUNT']),
                'item_ean': item['PRODUCT_ID']['bmecat:INTERNATIONAL_PID'],
                'item_description': item[
                    'PRODUCT_ID']['bmecat:DESCRIPTION_SHORT']
            }

        def search_purchase_order_line(ede_line=None):
            if ede_line['item_customer_id'] != int(item['LINE_ITEM_ID']):
                data = self.env['purchase.order.line'].search([
                    ('id', '=', ede_line['item_customer_id']),
                    ('order_id.name', 'ilike', ede_line[
                        'item_customer_ref'])
                ])
            else:
                data = self.env['purchase.order.line'].search([
                    ('order_id.ede_order_id', '=', ede_line[
                        'item_customer_ref']),
                    ('product_id.barcode', '=', item['PRODUCT_ID'][
                        'bmecat:INTERNATIONAL_PID'])
                ])
            if not data:
                data = self.env['purchase.order.line'].search([
                    ('order_id.name', '=', ede_line['item_customer_ref']),
                    ('product_id.barcode', '=', item[
                        'PRODUCT_ID']['bmecat:INTERNATIONAL_PID'])])
            if not data:
                return []
            if data.order_id not in orders:
                return []
            return data

        ede_ftp = orders[0].company_id.ede_ftp()
        ftp = ede_ftp.connection()
        files = ede_ftp.list_files(client=ftp)
        ede_log = self.env['account.invoice.ede.log'].create({
            'datetime': fields.Datetime.now(),
        })
        for file_name, file_info in files:
            file_fail = False
            line_msg = ''
            invoice_lines = []
            order_ids = []
            order_line_ids = []
            line_fail = False
            if file_name in ('.', '..'):
                continue
            _log.info('Process file: %s info: %s' % (file_name, file_info))
            xml = ede_ftp.process_xml_invoice(client=ftp, filename=file_name)
            ede_header = data_header_info(xml)
            exist_invoice = self.env['account.invoice'].search(
                [('reference', 'ilike', ede_header['invoice_id'])])
            if exist_invoice:
                _log.info('Invoice: %s is already created with id: %s' % (
                    ede_header['invoice_id'], (
                        exist_invoice and exist_invoice[0].id)))
                self.env['account.invoice.ede.log.line'].create({
                    'log_id': ede_log.id,
                    'ede_date_invoice': fields.Date.to_string(
                        ede_header['invoice_date']),
                    'ede_invoice_number': ede_header['invoice_id'],
                    'ede_xml_name': file_name,
                    'ede_xml_data': str(xml),
                    'state': 'done',
                    'log': line_msg,
                    'supplier_invoice_id':
                        exist_invoice and exist_invoice[0].id,
                })
                continue
            items = xml['INVOICE']['INVOICE_ITEM_LIST']['INVOICE_ITEM']
            items = isinstance(items, list) and items or [items]
            _log.info('Process invoice: %s date: %s' % (
                ede_header['invoice_id'], ede_header['invoice_date']))
            for item in items:
                ede_line = data_line_info(item)
                if not ede_line:
                    line_msg += _('No found line for item: %s\n') % item[
                        'PRODUCT_ID']['bmecat:DESCRIPTION_SHORT']
                    line_fail = True
                    continue
                order_line = search_purchase_order_line(ede_line)
                if not order_line:
                    line_msg += _('No found purchase line item: %s\n' % (
                        ede_line['item_description']))
                    line_fail = True
                    continue
                qty = order_line.qty_received - order_line.qty_invoiced
                if qty == 0.00:
                    line_msg += _('Order: %s Received qty: %s Invoice qty: %s '
                                  'Ede qty: %s to invoice: %s\n') % (
                        order_line.order_id.name, order_line.qty_received,
                        order_line.qty_invoiced, ede_line['item_quantity'],
                        qty,
                    )
                    line_fail = True
                    _log.info(
                        'Order: %s Received qty: %s Invoice qty: %s '
                        'Ede qty: %s to invoice: %s' % (
                            order_line.order_id.name, order_line.qty_received,
                            order_line.qty_invoiced, ede_line['item_quantity'],
                            qty,
                        )
                    )
                    continue
                invoice_lines.append({
                    'ede_line': ede_line,
                    'order_line': order_line,
                })
                order_ids.append(order_line.order_id.id)
                order_line_ids.append(order_line.id)
                if line_fail:
                    file_fail = True
            if not order_ids or not order_line_ids:
                line_msg += _('Not orders for invoice: %s' % ede_header[
                    'invoice_id'])
                _log.info(
                    'Not orders for invoice: %s' % ede_header['invoice_id'])
                file_fail = True
                if file_fail:
                    self.env['account.invoice.ede.log.line'].create({
                        'log_id': ede_log.id,
                        'ede_date_invoice': fields.Date.to_string(
                            ede_header['invoice_date']),
                        'ede_invoice_number': ede_header['invoice_id'],
                        'ede_xml_name': file_name,
                        'ede_xml_data': str(xml),
                        'state': 'fail',
                        'log': line_msg,
                    })
                    continue
            line_msg += _('Lines for invoice: %s is ok\n') % ede_header[
                'invoice_id']
            invoice = self.env['account.invoice'].create({
                'type': 'in_invoice',
                'reference': ede_header['invoice_id'],
                'journal_id': self.env.user.company_id.journal_id.id,
                'date_invoice': fields.Date.to_string(
                    ede_header['invoice_date']),
            })
            for order in self.env['purchase.order'].search(
                    [('id', 'in', list(set(order_ids)))]):
                invoice.write({
                    'purchase_id': order.id,
                    'origin': ", ".join([invoice.origin or '', order.name])
                })
                invoice.purchase_order_change()
            invoice._onchange_partner_id()
            invoice.mapped('invoice_line_ids').filtered(
                lambda l: l.purchase_line_id.id not in order_line_ids).unlink()
            for line in invoice_lines:
                inv_line = invoice.mapped('invoice_line_ids').filtered(
                    lambda l: l.purchase_line_id.id == line['order_line'].id)
                if not line:
                    continue
                if inv_line.quantity != line['ede_line']['item_quantity']:
                    inv_line.quantity = line['ede_line']['item_quantity']
                if inv_line.price_unit != line['ede_line']['item_price_fix']:
                    inv_line.price_unit = line['ede_line']['item_price_fix']
                taxes = inv_line.product_id.supplier_taxes_id.filtered(
                    (lambda r: r.company_id == invoice.company_id)
                    or inv_line.account_id.tax_ids
                    or self.invoice_id.company_id.account_purchase_tax_id)
                inv_line.invoice_line_tax_ids = (
                    invoice.fiscal_position_id.map_tax(
                        taxes, inv_line.product_id, invoice.partner_id))
                inv_line._onchange_account_id()
            invoice._onchange_partner_id()
            invoice.compute_taxes()
            self.env['account.invoice.ede.log.line'].create({
                'log_id': ede_log.id,
                'ede_date_invoice': fields.Date.context_today(self),
                'ede_invoice_number': ede_header['invoice_id'],
                'ede_xml_name': file_name,
                'ede_xml_data': str(xml),
                'log': line_msg,
                'supplier_invoice_id': invoice.id,
            })
            _log.info(
                'From Ede invoice: %s create Odoo invoice ID: %s:' % (
                    ede_header['invoice_id'], invoice.id))
            if self.env.user.company_id.ede_delete_done:
                ede_ftp.delete_file(client=ftp, filename=file_name)
                _log.info('Delete file: %s' % file_name)
            if self.env.user.company_id.ede_confirm_draft_invoice:
                _log.info('Confirm draft invoice id: %s' % invoice.id)
                invoice.action_invoice_open()

    @api.model
    def cron_ede_process_ftp_invoice(self):
        if not self.env.user.company_id.ede_use_ftp:
            _log.info('Please configure EDE FTP in company setup')
            return
        ede_supplier = self.env.user.company_id.ede_supplier_id
        orders_client = self.env['purchase.order'].search([
            ('partner_id', '=', ede_supplier.id),
            ('state', 'not in', ('done', 'cancel')),
            ('sale_order_id', '!=', None),
            ('is_ede_send', '=', True), ('ede_state', '=', 'C'),
            ('invoice_status', '=', 'to invoice'),
            ('ede_workflow_state', 'not in', (
                'draft', 'simulated', 'send'))], order='date_order desc')
        orders_company = self.env['purchase.order'].search([
            ('partner_id', '=', ede_supplier.id),
            ('is_ede_send', '=', True),
            ('state', 'not in', ('done', 'cancel')),
            ('sale_order_id', '!=', None),
            ('invoice_status', '=', 'to invoice')], order='date_order desc')
        if not orders_client + orders_company:
            return False
        self.ede_ftp_invoice(orders_client + orders_company)

    @api.multi
    def action_ede_ftp_invoice(self):
        for order in self:
            self.ede_ftp_invoice(order)
