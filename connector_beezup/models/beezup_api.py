###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
import logging
from datetime import datetime, timedelta

import requests
from odoo import _, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round

_log = logging.getLogger(__name__)


class BeezupApi(models.Model):
    _name = 'beezup.api'
    _description = 'Beezup Api'

    def get_beezup_order_data(self, order=False):
        company = self.env.user.company_id

        def get_response(page):
            data = {
                'pageNumber': page,
                'pageSize': 25,
                'storeIds': company.beezup_store_ids.split(','),
            }
            if order:
                data['marketplaceOrderIds'] = [order.origin]
            else:
                min_date = datetime.now() - timedelta(days=31)
                start_date = max(min_date, company.beezup_last_sync)
                data.update({
                    'beginPeriodUtcDate': start_date.strftime(
                        '%Y-%m-%dT%H:%M:%SZ'),
                    'endPeriodUtcDate': datetime.now().strftime(
                        '%Y-%m-%dT%H:%M:%SZ'),
                    'invoiceAvailabilityType': 'All',
                    'orderMerchantInfoSynchronizationStatus': 'All',
                })
            headers = {
                'Ocp-Apim-Subscription-Key': company.beezup_token,
                'content-type': 'application/json'
            }
            api_url = self.env['ir.config_parameter'].get_param(
                'beezup.api.url')
            return requests.post(
                url='%s/orders/v3/list/full' % api_url,
                headers=headers,
                data=json.dumps(data)
            )
        page = 1
        res = get_response(page)
        if res.status_code == 503:
            _log.error('Sync with Beezup not possible: %s' % res.reason)
            return False
        res_dict = json.loads(res.content)
        if res.status_code != 200:
            _log.error(res_dict['errors'][0]['message'])
            return False
        orders_data = res_dict['orders']
        if res_dict['paginationResult']['pageCount'] > 1:
            for page in range(
                    page, res_dict['paginationResult']['pageCount']):
                res_dict = json.loads(get_response(page + 1).content)
                orders_data += res_dict['orders']
        if not orders_data:
            _log.error('Sync with Beezup not possible, orders not found')
            return False
        if order and len(orders_data) > 1:
            _log.error(
                'Sync with Beezup not possible, more tan '
                'one order found for %s' % order.origin)
            return False
        return orders_data

    def sync_beezup_order_state(self, picking):
        company = self.env.user.company_id
        orders_data = self.get_beezup_order_data(picking.sale_id)
        if not orders_data:
            raise ValidationError(_(
                'Sync with Beezup not possible, see error log'))
        if len(orders_data) > 1:
            raise ValidationError(_(
                'Sync with Beezup not possible, more tan '
                'one order found for %s' % picking.sale_id.name))
        api_url = self.env['ir.config_parameter'].get_param('beezup.api.url')
        delivery_carrier_link = (
            self.env['delivery.carrier'].fixed_get_tracking_link(picking))
        data = {
            'order_Shipping_CarrierName': (
                picking.carrier_id and picking.carrier_id.name or False),
            'order_Shipping_ShippingUrl': delivery_carrier_link,
            'order_Shipping_ShipperTrackingNumber':
                picking.carrier_tracking_ref,
            'order_Shipping_FulfillmentDate': (
                picking.date_done.strftime('%Y-%m-%dT%H:%M:%SZ')),
        }
        order_data = orders_data[0]
        response = requests.post(
            url='%s/orders/v3/%s/%s/%s/ShipOrder' % (
                api_url, order_data['marketplaceTechnicalCode'],
                order_data['accountId'], order_data['beezUPOrderId']),
            headers={
                'Ocp-Apim-Subscription-Key': company.beezup_token,
                'content-type': 'application/json',
                'If-Match': order_data['etag'],
            },
            params={
                'userName': company.beezup_username,
                'testMode': company.beezup_test_mode,
            },
            data=json.dumps(data)
        )
        res_dict = json.loads(response.content)
        if response.status_code != 200:
            raise ValidationError(res_dict['errors'][0]['message'])
        return response.status_code

    def check_required_order_data(self, order):
        required_keys = [
            'marketplaceBusinessCode',
            'marketplaceTechnicalCode',
            'order_Buyer_AddressPostalCode',
            'order_MarketplaceOrderId',
            'order_Shipping_AddressLine1',
            'order_Shipping_AddressName',
            'order_Shipping_AddressPostalCode',
            'order_Status_BeezUPOrderStatus',
            'orderItems',
        ]
        errors = []
        for key in required_keys:
            if key not in order or order[key] is ('' or None):
                errors.append(key)
        return errors

    def search_fiscal_position(self, country):
        fiscal_positions = self.env['account.fiscal.position'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('country_id', '=', country.id),
        ])
        if not fiscal_positions:
            _log.error('No fiscal position found for country code \'%s\'.' % (
                country.code))
            return False
        elif len(fiscal_positions) > 1:
            _log.error('More than one fiscal position found for country code '
                       '\'%s\'.' % country.code)
            return False
        return fiscal_positions

    def get_fiscal_position(self, order):
        company = self.env.user.company_id
        property_account_position_id = (
            company.beezup_parent_partner_id
            and company.beezup_parent_partner_id.property_account_position_id)
        if company.beezup_force_partner and property_account_position_id:
            return property_account_position_id
        order_iso_code = order.get('order_Buyer_AddressCountryIsoCodeAlpha2')
        if not order_iso_code:
            _log.warn(
                'Country code empty not found for order %s; '
                '\'No country\' will be assigned.' % (
                    order['order_MarketplaceOrderId']))
            no_country = self.env.ref('import_template.no_country')
            return self.search_fiscal_position(no_country)
        if order_iso_code.upper() == 'ES':
            return company.beezup_fiscal_position_id
        else:
            countries = self.env['res.country'].search([
                ('code', '=', order_iso_code.upper()),
            ])
            if len(countries) > 1:
                _log.error(
                    'More than one country found for \'%s\'.' % order_iso_code)
                return False
            return (
                countries and self.search_fiscal_position(countries) or False)

    def get_price_without_taxs(self, price, fiscal_position, taxs):
        precision = self.env['decimal.precision'].precision_get(
            'Product Price')
        amount_taxs = sum(tax.amount / 100 for tax in taxs)
        return float_round(price / (1 + amount_taxs), precision)

    def get_shipping_line_data(self, shipping_price, fiscal_position):
        company = self.env.user.company_id
        taxs = fiscal_position.map_tax(
            company.beezup_shipping_product_id.taxes_id)
        price_without_taxs = self.get_price_without_taxs(
            shipping_price, fiscal_position, taxs)
        return {
            'name': company.beezup_shipping_product_id.name,
            'product_id': company.beezup_shipping_product_id.id,
            'price_unit': price_without_taxs,
            'product_uom_qty': 1,
            'tax_id': [(6, 0, [t.id for t in taxs])],
        }

    def get_payment_method(self, bz_payment_method):
        methods = self.env['account.payment.method'].search([
            '|',
            ('name', '=', bz_payment_method),
            ('code', '=', bz_payment_method),
        ], limit=1).id
        return methods

    def register_payment(
            self, bz_payment_method, invoice, journal, payment_date):
        payment_method = (
            self.get_payment_method(bz_payment_method)
            or self.env.ref('account.account_payment_method_manual_in').id)
        data = {
            'payment_method_id': payment_method,
            'journal_id': journal.id,
        }
        if payment_date:
            data['payment_date'] = payment_date
        payment = self.env['account.payment'].with_context(
            active_model='account.invoice',
            active_id=invoice.id,
            active_ids=invoice.ids,
        ).create(data)
        payment.action_validate_invoice_payment()

    def confirm_picking(self, picking_out, order, picking_date):
        picking_out.action_confirm()
        picking_out.action_assign()
        for move in picking_out.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_out.action_done()
        if picking_out.state != 'done':
            _log.warn(
                'The picking out associated with the order with origin \'%s\' '
                'has not been transferred correctly, check manually.' % (
                    order.origin))
            return False
        if picking_date:
            picking_out.write({'date_done': picking_date})

    def create_return_pickings(self, pickings, order):
        for picking in pickings:
            picking_wizard = self.env['stock.return.picking'].with_context(
                active_id=picking.id,
                active_ids=picking.ids,
                active_model='stock.picking',
            ).create({})
            for return_line in picking_wizard.product_return_moves:
                return_line.to_refund = True
            picking_return_action = picking_wizard.create_returns()
            picking_return = self.env['stock.picking'].browse(
                picking_return_action['res_id'])
            if not picking_return:
                _log.warn(
                    'The picking return associated with the order with origin '
                    '\'%s\' has not been created correctly, check manually.' %
                    (order.origin))
                return False
            for move in picking_return.move_lines:
                move.move_line_ids[0].qty_done = move.product_qty
            picking_return.action_done()
            if picking_return.state != 'done':
                _log.warn(
                    'The picking return associated with the order with origin '
                    '\'%s\' has not been transferred correctly, check '
                    'manually.' % order.origin)
                return False

    def get_beezup_statuses(self):
        return {
            'NEW': 'paid',
            'INPROGRESS': 'paid',
            'PENDING': 'paid',
            'TOSHIP': 'paid',
            'SHIPPING': 'paid',
            'SHIPPED': 'shipped',
            'CLOSED': 'delivered',
            'CANCELLED': 'cancelled',
            'ABORTED': 'cancelled',
            'USERCANCELLED': 'cancelled',
        }

    def create_invoice_refund(self, invoice):
        if invoice.reconciled:
            invoice.move_id.line_ids.remove_move_reconcile()
        refund_wiz = self.env['account.invoice.refund'].with_context({
            'active_id': invoice.id,
            'active_ids': invoice.ids,
            'active_model': 'account.invoice',
        }).create({
            'description': 'Beezup cancel',
            'filter_refund': 'cancel',
        })
        refund_wiz.invoice_refund()

    def process_order(self, bz_order, order):
        bz_status = bz_order['order_Status_BeezUPOrderStatus'].upper()
        order_bz_status = self.get_beezup_statuses().get(bz_status)
        if not order_bz_status:
            _log.warn(
                'Order \'%s\' status \'%s\' unrecognized, will not be '
                'proccesed' % (order.origin, bz_status))
            return False
        if order.state_beezup == order_bz_status:
            return False
        order.write({
            'state_beezup': bz_status,
            'etag_beezup': bz_order['etag']
        })
        if order_bz_status == 'cancelled':
            for invoice in order.invoice_ids:
                if invoice.state == 'cancel':
                    continue
                elif invoice.state in ['draft', 'open']:
                    invoice.action_cancel()
                else:
                    self.create_invoice_refund(invoice)
            if not any(
                    picking.state == 'done' for picking in order.picking_ids):
                order.action_cancel()
            else:
                done_pickings = order.picking_ids.filtered(
                    lambda m: m.state == 'done')
                self.create_return_pickings(done_pickings)
            return True
        elif order_bz_status in ['shipped', 'delivered']:
            if not order.picking_ids:
                _log.warn(
                    'The order with origin \'%s\' has not generated picking, '
                    'check manually.' % order.origin)
                return False
            if len(order.picking_ids) > 1:
                _log.warn(
                    'The order with origin \'%s\' has more than one picking '
                    'associated, check manually.' % order.origin)
                return False
            picking_out = order.picking_ids[0]
            if picking_out.state not in ['done', 'cancel']:
                picking_date = (
                    bz_order.get('order_Shipping_EarliestShipUtcDate')
                    and datetime.strptime(
                        bz_order['order_Shipping_EarliestShipUtcDate'],
                        '%Y-%m-%dT%H:%M:%SZ')
                    or False)
                if picking_date:
                    picking_out.scheduled_date = picking_date
                if picking_out.picking_type_code != 'outgoing':
                    _log.warn(
                        'The picking associated with the order with origin '
                        '\'%s\' is not of type output associated, check '
                        'manually.' % (order.origin))
                    return False
            self.confirm_picking(picking_out, order, picking_date)
        return True

    def create_beezup_partner(self, bz_order):
        company = self.env.user.company_id
        zip = self.env['res.city.zip'].search([
            ('name', '=', bz_order['order_Buyer_AddressPostalCode'])
        ], limit=1)
        partner_data = {
            'city': zip and zip.city_id.name or False,
            'city_id': zip and zip.city_id.id or False,
            'country_id': zip and zip.city_id.country_id.id or False,
            'customer': True,
            'email': bz_order.get('order_Buyer_Email'),
            'name': bz_order['order_Shipping_AddressName'],
            'phone': bz_order.get('order_Buyer_Phone'),
            'state_id': zip and zip.city_id.state_id.id or False,
            'street': bz_order.get('order_Buyer_AddressLine1'),
            'street2': bz_order.get('order_Buyer_AddressLine2'),
            'zip': zip and zip.name or False,
            'zip_id': zip.id,
            'property_account_receivable_id': (
                company.beezup_partner_account_id.id),
        }
        parent_partner_id = company.beezup_parent_partner_id
        if company.beezup_force_partner:
            partner_data['parent_id'] = parent_partner_id.id
            partner_data['vat'] = company.beezup_parent_partner_id.vat
        partner_data['property_account_position_id'] = (
            company.beezup_force_partner
            and parent_partner_id.property_account_position_id.id
            or company.beezup_fiscal_position_id.id),
        return self.env['res.partner'].create(partner_data)

    def create_beezup_partner_shipping(self, bz_order, parent):
        zip = self.env['res.city.zip'].search([
            ('name', '=', bz_order['order_Shipping_AddressPostalCode'])
        ], limit=1)
        partner_ship_data = {
            'city': zip and zip.city_id.name or False,
            'city_id': zip and zip.city_id.id or False,
            'country_id': zip and zip.city_id.country_id.id or False,
            'name': bz_order['order_Shipping_AddressName'],
            'parent_id': parent.id,
            'phone': bz_order.get('order_Shipping_Phone'),
            'state_id': zip and zip.city_id.state_id.id or False,
            'street': bz_order['order_Shipping_AddressLine1'],
            'street2': bz_order.get('order_Shipping_AddressLine2'),
            'type': 'delivery',
            'zip': zip and zip.name or False,
            'zip_id': zip.id,
        }
        return self.env['res.partner'].create(partner_ship_data)

    def create_order_lines(self, bz_order, sale_order, fiscal_position):
        order_lines = []
        for item in bz_order['orderItems']:
            product = self.env['product.product'].search([
                ('default_code', '=', item['orderItem_MerchantProductId'])
            ], limit=1)
            if not product:
                beezup_taxs = self.env.user.company_id.beezup_tax_ids
                list_price_wo_taxs = self.get_price_without_taxs(
                    item['orderItem_ItemPrice'], fiscal_position, beezup_taxs)
                product = product.create({
                    'default_code': item['orderItem_MerchantProductId'],
                    'name': item['orderItem_Title'],
                    'type': 'product',
                    'invoice_policy': 'order',
                    'list_price': list_price_wo_taxs,
                })
                _log.info('Product created, %s' % product.name)
            taxs = fiscal_position.map_tax(product.taxes_id)
            price_without_taxs = self.get_price_without_taxs(
                item['orderItem_ItemPrice'], fiscal_position, taxs)
            order_lines.append((0, 0 , {
                'order_id': sale_order.id,
                'product_id': product.id,
                'product_uom_qty': item['orderItem_Quantity'],
                'price_unit': price_without_taxs,
                'tax_id': [(6, 0, [t.id for t in taxs])],
            }))
        if bz_order['order_Shipping_Price']:
            shipping_line = self.get_shipping_line_data(
                bz_order['order_Shipping_Price'], fiscal_position)
            order_lines.append((0, 0 , shipping_line))
        if order_lines:
            sale_order.write({'order_line': order_lines})

    def create_beezup_sale_order(self, bz_order):
        res_partner_obj = self.env['res.partner']
        bz_order_id = bz_order['order_MarketplaceOrderId']
        partner = res_partner_obj.search([
            ('name', '=', bz_order['order_Shipping_AddressName']),
            ('email', '=', bz_order.get('order_Buyer_Email')),
            ('type', '=', 'contact'),
        ], limit=1)
        if any(
                not item.get('orderItem_ItemPrice')
                for item in bz_order['orderItems']
        ):
            _log.error('Any item in order \'%s\' has not price' % bz_order_id)
            return False
        if not partner:
            partner = self.create_beezup_partner(bz_order)
        shipping_address = bz_order['order_Shipping_AddressLine1']
        partner_shipping = False
        if shipping_address != partner.street:
            partner_shipping = res_partner_obj.search([
                ('name', '=', bz_order['order_Shipping_AddressName']),
                ('email', '=', bz_order.get('order_Buyer_Email')),
                ('street', '=', shipping_address),
                ('type', '=', 'delivery'),
            ], limit=1)
            if not partner_shipping:
                partner_shipping = self.create_beezup_partner_shipping(
                    bz_order, partner)
        fiscal_position = self.get_fiscal_position(bz_order)
        if not fiscal_position:
            _log.error(
                'Fiscal position not found for order \'%s\', '
                'country ISO: \'%s\'' % (bz_order_id, bz_order.get(
                    'order_Buyer_AddressCountryIsoCodeAlpha2', '-')
                )
            )
            return False
        crm_team_obj = self.env['crm.team']
        crm_team = crm_team_obj.search([
            ('name', '=', bz_order['marketplaceBusinessCode'])], limit=1)
        if not crm_team:
            crm_team = crm_team_obj.create({
                'name': bz_order['marketplaceBusinessCode'],
            })
        company = self.env.user.company_id
        carrier_id = (
            bz_order['order_Shipping_Method']
            and self.env['delivery.carrier'].search([
                ('name', '=', bz_order['order_Shipping_Method'])], limit=1).id
            or company.beezup_carrier_id.id)
        order_data = {
            'name': bz_order_id,
            'origin': bz_order_id,
            'url_beezup': bz_order.get('beezUPOrderUrl'),
            'pricelist_id': company.beezup_pricelist_id.id,
            'payment_mode_id': company.beezup_payment_mode_id.id,
            'date_order': bz_order['order_PurchaseUtcDate'],
            'carrier_id': carrier_id,
            'partner_id': partner.id,
            'team_id': crm_team.id,
            'partner_invoice_id': (
                company.beezup_force_partner
                and company.beezup_parent_partner_id.id or partner.id),
            'partner_shipping_id': (
                partner_shipping and partner_shipping.id or partner.id),
            'from_import_sale_beezup': True,
        }
        sale_order = self.env['sale.order'].create(order_data)
        self.create_order_lines(bz_order, sale_order, fiscal_position)
        _log.info('Beezup sale order %s created' % sale_order.id)
        self.confirm_sale_order(bz_order, sale_order)
        self.process_order(bz_order, sale_order)
        return sale_order

    def confirm_sale_order(self, bz_order, sale_order):
        invoice_policy = list(set(sale_order.order_line.filtered(
            lambda ln: ln.product_id.type != 'service').mapped(
            'product_id.invoice_policy')))
        if invoice_policy != ['order']:
            _log.warn(
                'The invoice policy of the products of order with origin '
                '\'%s\' is %s and is not contemplated. It must be \'order\''
                ', so the pickings and the invoice has not been created; check'
                ' manually.' % (sale_order.origin, invoice_policy))
            return False
        sale_order.action_confirm()
        sale_order.action_invoice_create()
        invoices = sale_order.invoice_ids
        if not invoices:
            _log.warn(
                'The order with origin \'%s\' has not generated invoice; '
                'check manually.' % sale_order.origin)
            return False
        if len(invoices) > 1:
            _log.warn(
                'More than one invoice has been generated from the order with '
                'origin \'%s\'; check manually.' % sale_order.origin)
            return False
        invoice = invoices[0]
        invoice.action_invoice_open()
        if invoice.state != 'open':
            _log.warn(
                'The invoice associated with the order with origin \'%s\' has '
                'not been opened correctly, check manually.' % (
                    sale_order.origin))
            return False
        payment_date = (
            bz_order.get('order_PayingUtcDate')
            and datetime.strptime(
                bz_order['order_PayingUtcDate'], '%Y-%m-%dT%H:%M:%SZ')
            or False)
        company = self.env.user.company_id
        bz_payment_method = bz_order.get('order_PaymentMethod')
        self.register_payment(
            bz_payment_method, invoice, company.beezup_journal_payment_id,
            payment_date)
        if invoice.state != 'paid':
            _log.warn(
                'The invoice associated with the order with origin \'%s\' has '
                'not been paid correctly, check manually.' % sale_order.origin)
            return False

    def import_beezup_orders(self):
        error_count = 0
        skip_count = 0
        company = self.env.user.company_id
        beezup_orders = self.get_beezup_order_data()
        if not beezup_orders:
            _log.error('Sync with Beezup not possible, see error log')
            return False
        _log.info('%s Beezup orders will be imported' % len(beezup_orders))
        for order_count, bz_order in enumerate(beezup_orders):
            bz_order_id = bz_order['order_MarketplaceOrderId']
            _log.info('%s/%s %s' % (
                order_count + 1, len(beezup_orders), bz_order_id))
            sale_orders = self.env['sale.order'].search([
                ('origin', 'ilike', bz_order_id)])
            errors = False
            if len(sale_orders) > 1:
                _log.warn(
                    'More than one sale order with origin \'%s\' '
                    'has been found. The order details could not be '
                    'updated.' % bz_order_id)
                skip_count += 1
            elif not sale_orders:
                errors = self.check_required_order_data(bz_order)
                if errors:
                    _log.error(
                        'Sale order \'%s\' has not required fields: %s' % (
                            bz_order_id, ', '.join(errors)))
                    error_count += 1
                    continue
                sale_orders = self.create_beezup_sale_order(bz_order)
                if not sale_orders:
                    _log.error('Sale order \'%s\' not created, see error '
                               'log' % bz_order_id)
                    error_count += 1
                    continue
            else:
                if sale_orders.etag_beezup == bz_order['etag']:
                    _log.info(
                        'No changes in \'%s\', skiped' % bz_order_id)
                    continue
                proccessed = self.process_order(bz_order, sale_orders)
                if not proccessed:
                    _log.info(
                        'Order with origin \'%s\' already in database, '
                        'skiped' % bz_order_id)
                    skip_count += 1
        company.beezup_last_sync = datetime.now()
        _log.info('Beezup import complete, %s errors, %s skiped' % (
            error_count, skip_count))
        return True

    def sync_beezup_orders_state(self):
        error_count = 0
        orders_done = self.env['sale.order'].search([
            ('state', '=', 'sale'),
            ('from_import_sale_beezup', '=', True),
        ])
        for order_count, order in enumerate(orders_done):
            _log.info('%s/%s %s' % (
                order_count + 1, len(orders_done), order.origin))
            orders_data = self.get_beezup_order_data(order)
            if not orders_data:
                _log.error(
                    'Sync with Beezup not possible, order not found: %s' % (
                        order.origin))
                error_count += 1
                continue
            elif len(orders_data) > 1:
                _log.error(
                    'Sync with Beezup not possible, more tan '
                    'one order found for %s' % order.name)
                error_count += 1
                continue
            else:
                if orders_data[0]['etag'] == order.etag_beezup:
                    continue
                errors = self.check_required_order_data(orders_data[0])
                if errors:
                    _log.error('Sale order %s has not required fields: %s' % (
                        orders_data[0]['order_MarketplaceOrderId'], ', '.join(
                            errors)))
                    error_count += 1
                    continue
                self.process_order(orders_data[0], order)
        _log.info('Beezup sync complete, %s errors' % error_count)
        return True
