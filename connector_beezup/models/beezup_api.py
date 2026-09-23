###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json
import logging
import re
from datetime import datetime, timedelta

import requests
from odoo import _, models
from odoo.tools.float_utils import float_round

_log = logging.getLogger(__name__)


class BeezupApi(models.Model):
    _name = 'beezup.api'
    _description = 'Beezup Api'

    def savepoint(self, name):
        self._cr.execute('SAVEPOINT %s' % name)

    def rollback(self, name):
        self._cr.execute('ROLLBACK TO SAVEPOINT %s' % name)
        self.pool.clear_caches()
        self.pool.reset_changes()

    def release(self, name):
        self._cr.execute('RELEASE SAVEPOINT %s' % name)

    def clean_zip(self, zip_value, country_iso_code):
        if not isinstance(zip_value, float):
            zip_value = re.sub('[^0-9]', '', str(zip_value))
        if country_iso_code == 'ES' and zip_value:
            zip_value = zip_value.zfill(5)
        return zip_value or ''

    def get_country_iso_code(self, bz_order):
        country_iso_code = bz_order.get(
            'order_Buyer_AddressCountryIsoCodeAlpha2',
            bz_order.get('order_Buyer_AddressCountryName', False))
        return country_iso_code and country_iso_code.upper() or False

    def get_beezup_order_data(self, order=False):
        company = self.env.user.company_id

        def get_response(page):
            if not company.beezup_store_ids:
                return _('Beezup store not set')
            data = {
                'pageNumber': page,
                'pageSize': 25,
                'storeIds': company.beezup_store_ids.split(','),
            }
            if order:
                data['marketplaceOrderIds'] = [order.origin]
            else:
                min_date = datetime.now() - timedelta(days=31)
                min_period = datetime.now() - timedelta(
                    days=company.min_days_to_sync)
                start_date = max(
                    min_date, min(min_period, company.beezup_last_sync))
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
        result_dict = {'errors': []}
        res = get_response(page)
        if isinstance(res, str):
            result_dict['errors'].append(res)
            return result_dict
        if res.status_code == 503:
            msg_error = (_('Sync with Beezup not possible: %s') % res.reason)
            result_dict['errors'].append(msg_error)
            _log.error(msg_error)
            return result_dict
        res_dict = json.loads(res.content)
        if res.status_code != 200:
            error_msgs = res_dict.get('errors', [])
            for error_msg in error_msgs:
                msg_error = error_msg.get('message', None)
                result_dict['errors'].append(msg_error)
                _log.error(msg_error)
            return result_dict
        orders_data = res_dict['orders']
        if res_dict['paginationResult']['pageCount'] > 1:
            for page in range(
                    page, res_dict['paginationResult']['pageCount']):
                res_dict = json.loads(get_response(page + 1).content)
                orders_data += res_dict['orders']
        if not orders_data:
            _log.warn('Sync with Beezup not possible, orders not found')
            return False
        if order and len(orders_data) > 1:
            msg_error = (_(
                'Sync with Beezup not possible, more tan one order found for '
                '%s') % order.origin)
            result_dict['errors'].append(msg_error)
            _log.error(msg_error)
        else:
            result_dict['orders'] = orders_data
        return result_dict

    def sync_beezup_order_state(self, picking):
        company = self.env.user.company_id
        beezup_data = self.get_beezup_order_data(picking.sale_id)
        if not beezup_data:
            return
        errors = beezup_data.get('errors')
        orders_data = beezup_data.get('orders')
        if errors:
            body = (_('Sync state with Beezup not possible: %s') % (
                ', '.join(errors)))
            picking.message_post(body=body)
            return
        if len(orders_data) > 1:
            body = (_(
                'Sync state with Beezup not possible, more tan '
                'one order found for %s' % picking.sale_id.name))
            picking.message_post(body=body)
            return
        order_data = orders_data[0]
        order_state = order_data.get(
            'order_Status_BeezUPOrderStatus', '').lower()
        if 'shipped' in order_state:
            return
        api_url = self.env['ir.config_parameter'].get_param('beezup.api.url')
        delivery_carrier_link = (
            picking.carrier_id
            and picking.carrier_id.fixed_get_tracking_link(picking) or False)
        data = {
            'order_Shipping_CarrierName': (
                picking.carrier_id and picking.carrier_id.name or False),
            'order_Shipping_ShippingUrl': delivery_carrier_link,
            'order_Shipping_ShipperTrackingNumber':
                picking.carrier_tracking_ref,
            'order_Shipping_FulfillmentDate': (
                picking.date_done.strftime('%Y-%m-%dT%H:%M:%SZ')),
        }
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
            body = (_('Beezup state update error: %s') % (
                res_dict['errors'][0]['message']))
            picking.message_post(body=body)
        return response.status_code

    def check_required_order_data(self, order):
        required_keys = [
            'marketplaceBusinessCode',
            'marketplaceTechnicalCode',
            'order_Buyer_AddressCity',
            'order_Buyer_AddressPostalCode',
            'order_MarketplaceOrderId',
            'order_PurchaseUtcDate',
            'order_Shipping_AddressCountryIsoCodeAlpha2',
            'order_Shipping_AddressName',
            'order_Shipping_AddressPostalCode',
            'order_Status_BeezUPOrderStatus',
            'orderItems',
        ]
        errors = []
        for key in required_keys:
            if key not in order or order[key] is ('' or None):
                errors.append(key)
        shipping_address = order.get(
            'order_Shipping_AddressLine1',
            order.get('order_Shipping_AddressLine2', order.get(
                'order_Shipping_AddressLine3', False)))
        if not shipping_address:
            errors.append('order_Shipping_AddressLine')
        buyer_country_code = order.get(
            'order_Buyer_AddressCountryIsoCodeAlpha2',
            order.get('order_Buyer_AddressCountryName', False))
        if not buyer_country_code:
            errors.append('order_Buyer_AddressCountryIsoCodeAlpha2')
        return errors

    def search_fiscal_position(self, country, zip):
        company = self.env.user.company_id
        domain = [
            ('auto_apply', '=', True),
            ('country_id', '=', country.id),
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
        ]
        if country.id == self.env.ref('base.es').id:
            if (zip and zip.city_id.state_id
                    and zip.city_id.state_id.code in ['CE', 'ME', 'GC']):
                domain.insert(0, ('state_ids', 'in', zip.city_id.state_id.id))
            else:
                return company.beezup_fiscal_position_id
        fiscal_positions = self.env['account.fiscal.position'].search(domain)
        if not fiscal_positions:
            _log.error('No fiscal position found for country code \'%s\'.' % (
                country.code))
            return False
        elif len(fiscal_positions) > 1:
            _log.error(
                'More than one fiscal position found for country code  '
                '\'%s\'.' % country.code)
            return False
        return fiscal_positions

    def get_fiscal_position(self, order, zip):
        company = self.env.user.company_id
        property_account_position_id = (
            company.beezup_parent_partner_id
            and company.beezup_parent_partner_id.property_account_position_id
            or False)
        if company.beezup_force_partner and property_account_position_id:
            return property_account_position_id
        order_iso_code = zip and zip.city_id.country_id.code or order.get(
            'order_Shipping_AddressCountryIsoCodeAlpha2', False)
        if not order_iso_code:
            _log.warn(
                'Country code empty not found for order %s; '
                '\'No country\' will be assigned.' % (
                    order['order_MarketplaceOrderId']))
            no_country = self.env.ref('import_template.no_country')
            return self.search_fiscal_position(no_country, zip)
        countries = self.env['res.country'].search([
            ('code', '=', order_iso_code.upper()),
        ])
        if len(countries) > 1:
            _log.error(
                'More than one country found for \'%s\'.' % order_iso_code)
            return False
        return (
            countries
            and self.search_fiscal_position(countries, zip)
            or False)

    def get_price_without_taxs(self, price, fiscal_position, taxs):
        precision = self.env['decimal.precision'].precision_get(
            'Product Price')
        amount_taxs = sum(tax.amount / 100 for tax in taxs)
        return float_round(price / (1 + amount_taxs), precision)

    def get_shipping_line_data(self, order_id, shipping_price, fiscal_position):
        company = self.env.user.company_id
        taxs = fiscal_position.map_tax(
            company.beezup_shipping_product_id.taxes_id)
        price_without_taxs = self.get_price_without_taxs(
            shipping_price, fiscal_position, taxs)
        return {
            'name': company.beezup_shipping_product_id.name,
            'product_id': company.beezup_shipping_product_id.id,
            'order_id': order_id,
            'price_unit': price_without_taxs,
            'product_uom_qty': 1,
            'tax_id': [(6, 0, [t.id for t in taxs])],
            'is_delivery': True,
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
        company = self.env.user.company_id
        if not company.picking_auto_done:
            return
        picking_out.action_done()
        if picking_out.state != 'done':
            return (_(
                'The picking out associated with the order with origin \'%s\' '
                'has not been transferred correctly, check manually.') % (
                    order.origin))
        msg = _('Picking processed from Beezup order: %s') % order.origin
        picking_out.message_post(body=msg)
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
                return_line.to_refund = False
            picking_return_action = picking_wizard.create_returns()
            picking_return = self.env['stock.picking'].browse(
                picking_return_action['res_id'])
            if not picking_return:
                return (_(
                    'The picking return associated with the order with origin '
                    '\'%s\' has not been created correctly, check manually.') %
                    order.origin)
            for move in picking_return.move_lines:
                move.move_line_ids[0].qty_done = move.product_qty
            picking_return.action_done()
            if picking_return.state != 'done':
                return (_(
                    'The picking return associated with the order with origin '
                    '\'%s\' has not been transferred correctly, check '
                    'manually.') % order.origin)

    def get_beezup_statuses(self):
        return {
            'NEW': 'new',
            'INPROGRESS': 'paid',
            'PENDING': 'paid',
            'TOSHIP': 'paid',
            'SHIPPING': 'shipped',
            'SHIPPED': 'shipped',
            'CLOSED': 'delivered',
            'CANCELLED': 'cancelled',
            'CANCELED': 'cancelled',
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
        errors = []
        bz_status = bz_order['order_Status_BeezUPOrderStatus'].upper()
        order_bz_status = self.get_beezup_statuses().get(bz_status)
        if not order_bz_status:
            errors.append(_(
                'Order \'%s\' status \'%s\' unrecognized, will not be '
                'processed') % (order.origin, bz_status))
            return errors
        if order.state_beezup == bz_status:
            return errors
        order_data = {
            'state_beezup': bz_status,
            'etag_beezup': bz_order['etag'],
        }
        if bz_order.get('order_PurchaseUtcDate'):
            order_data['confirmation_date'] = datetime.strptime(
                bz_order['order_PurchaseUtcDate'], '%Y-%m-%dT%H:%M:%SZ')
        order.write(order_data)
        if order_bz_status == 'cancelled':
            if not order.team_id.beezup_auto_cancel_orders:
                return errors
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
                return_piking_error = self.create_return_pickings(done_pickings)
                if return_piking_error:
                    errors += return_piking_error
        elif order_bz_status in ['shipped', 'delivered']:
            if not order.picking_ids:
                errors.append(_(
                    'The order with origin \'%s\' has not generated picking, '
                    'check manually.') % order.origin)
                return errors
            if len(order.picking_ids) > 1:
                errors.append(_(
                    'The order with origin \'%s\' has more than one picking '
                    'associated, check manually.') % order.origin)
                return errors
            picking_out = order.picking_ids[0]
            if picking_out.state not in ['done', 'cancel']:
                picking_date = (
                    bz_order.get('order_Shipping_EarliestShipUtcDate')
                    and datetime.strptime(
                        bz_order['order_Shipping_EarliestShipUtcDate'].split(
                            'Z')[0].split('.')[0],
                        '%Y-%m-%dT%H:%M:%S')
                    or False)
                if picking_date:
                    picking_out.scheduled_date = picking_date
                if picking_out.picking_type_code != 'outgoing':
                    errors.append(_(
                        'The picking associated with the order with origin '
                        '\'%s\' is not of type output associated, check '
                        'manually.') % order.origin)
                    return errors
                if order.team_id.beezup_picking_policy == 'automatic':
                    picking_error = self.confirm_picking(
                        picking_out, order, picking_date)
                    if picking_error:
                        errors += picking_error
        return errors

    def create_beezup_partner(self, bz_order):
        company = self.env.user.company_id
        country_iso_code = self.get_country_iso_code(bz_order)
        clean_zip = self.clean_zip(
            bz_order['order_Buyer_AddressPostalCode'], country_iso_code)
        zip_domain = [
            ('name', '=', clean_zip),
        ]
        if country_iso_code:
            zip_domain += [
                ('city_id.country_id.code', '=', country_iso_code),
            ]
        zip = self.env['res.city.zip'].search(zip_domain, limit=1)
        country_id = bz_state_region_id = False
        if not zip:
            country_id = self.env['res.country'].search([
                ('code', '=', country_iso_code),
            ], limit=1).id
            bz_state_region = bz_order.get(
                'order_Shipping_AddressStateOrRegion', False)
            if bz_state_region:
                bz_state_region_id = self.env['res.country.state'].search([
                    ('name', '=', bz_state_region),
                ], limit=1).id
        partner_data = {
            'city': zip and zip.city_id.name or bz_order.get(
                'order_Buyer_AddressCity', ''),
            'city_id': zip and zip.city_id.id or False,
            'country_id': zip and zip.city_id.country_id.id or country_id,
            'customer': True,
            'email': bz_order.get('order_Buyer_Email'),
            'name': bz_order['order_Shipping_AddressName'],
            'phone': bz_order.get('order_Buyer_Phone'),
            'state_id': zip and zip.city_id.state_id.id or bz_state_region_id,
            'street': bz_order.get('order_Buyer_AddressLine1'),
            'street2': ' '.join([
                bz_order.get('order_Buyer_AddressLine2') or '',
                bz_order.get('order_Buyer_AddressLine3') or '',
            ]),
            'zip': zip and zip.name or bz_order.get(
                'order_Buyer_AddressPostalCode', ''),
            'zip_id': zip.id,
            'property_account_receivable_id': (
                company.beezup_partner_account_id.id),
        }
        fiscal_position = self.get_fiscal_position(bz_order, zip)
        parent_partner_id = company.beezup_parent_partner_id
        if company.beezup_force_partner:
            partner_data['parent_id'] = parent_partner_id.id
            partner_data['vat'] = company.beezup_parent_partner_id.vat
        partner_data['property_account_position_id'] = (
            company.beezup_force_partner
            and parent_partner_id.property_account_position_id.id
            or fiscal_position and fiscal_position.id
            or company.beezup_fiscal_position_id.id)
        return self.env['res.partner'].create(partner_data)

    def create_beezup_partner_shipping(self, bz_order, parent):
        country_iso_code = (
            bz_order.get('order_Shipping_AddressCountryIsoCodeAlpha2')
            and bz_order['order_Shipping_AddressCountryIsoCodeAlpha2'].upper()
            or False)
        clean_zip = self.clean_zip(
            bz_order['order_Shipping_AddressPostalCode'], country_iso_code)
        zip_domain = [
            ('name', '=', clean_zip),
        ]
        if country_iso_code:
            zip_domain += [
                ('city_id.country_id.code', '=', country_iso_code),
            ]
        zip = self.env['res.city.zip'].search(zip_domain, limit=1)
        country_id = bz_state_region_id = False
        if not zip:
            country_id = self.env['res.country'].search([
                ('code', '=', country_iso_code),
            ], limit=1).id
            bz_state_region = bz_order.get(
                'order_Shipping_AddressStateOrRegion', False)
            if bz_state_region:
                bz_state_region_id = self.env['res.country.state'].search([
                    ('name', '=', bz_state_region),
                ], limit=1).id
        street1 = bz_order.get('order_Shipping_AddressLine1', None)
        street2 = ' '.join(
            [
                bz_order.get('order_Shipping_AddressLine2') or '',
                bz_order.get('order_Shipping_AddressLine3') or ''
            ])
        partner_ship_data = {
            'city': zip and zip.city_id.name or bz_order.get(
                'order_Shipping_AddressCity', ''),
            'city_id': zip and zip.city_id.id or False,
            'country_id': zip and zip.city_id.country_id.id or country_id,
            'name': bz_order['order_Shipping_AddressName'],
            'parent_id': parent.id,
            'phone': bz_order.get('order_Shipping_Phone'),
            'state_id': zip and zip.city_id.state_id.id or bz_state_region_id,
            'street': street1 or street2,
            'street2': street1 and street2 or None,
            'type': 'delivery',
            'zip': zip and zip.name or bz_order.get(
                'order_Shipping_AddressPostalCode', ''),
            'zip_id': zip.id,
        }
        return self.env['res.partner'].create(partner_ship_data)

    def _create_with_onchange(self, record, values):
        onchange_specs = {
            field_name: '1' for field_name, field in record._fields.items()
        }
        data = self._add_missing_default_values({})
        data.update(values)
        new = record.new(data)
        new._origin = record
        res = {'value': {}, 'warnings': set()}
        for field in record._onchange_spec():
            if onchange_specs.get(field):
                new._onchange_eval(field, onchange_specs[field], res)
        cache = record._convert_to_write(new._cache)
        cache.update(values)
        return record.create(cache)

    def create_order_lines(self, bz_order, sale_order, fiscal_position):
        line_obj = self.env['sale.order.line']
        log = []
        for item in bz_order['orderItems']:
            product = self.env['product.product'].search([
                ('default_code', '=', item['orderItem_MerchantProductId']),
            ], limit=1)
            if not product:
                info = self.env['product.supplierinfo'].search([
                    ('product_code', '=', item['orderItem_MerchantProductId']),
                ], limit=1)
                if info:
                    product = (
                        info.product_id and info.product_id
                        or info.product_tmpl_id.product_variant_id)
            if not product:
                beezup_taxs = self.env.user.company_id.beezup_tax_ids
                list_price_wo_taxs = self.get_price_without_taxs(
                    item['orderItem_ItemPrice'], fiscal_position, beezup_taxs)
                default_invoice_policy = (
                    self.env['product.product'].default_get(
                        ['invoice_policy']).get('invoice_policy'))
                product = product.create({
                    'default_code': item['orderItem_MerchantProductId'],
                    'name': item['orderItem_Title'],
                    'type': 'product',
                    'invoice_policy': default_invoice_policy,
                    'list_price': list_price_wo_taxs,
                })
                log.append(_('Product created from Beezup, %s') % product.name)
                _log.warn(log)
            taxs = fiscal_position.map_tax(product.taxes_id)
            price_without_taxs = self.get_price_without_taxs(
                item['orderItem_ItemPrice'], fiscal_position, taxs)
            line_data = {
                'order_id': sale_order.id,
                'product_id': product.id,
                'product_uom_qty': item['orderItem_Quantity'],
                'price_unit': price_without_taxs,
                'tax_id': [(6, 0, [t.id for t in taxs])],
            }
            self._create_with_onchange(line_obj, line_data)
        sale_order.get_delivery_price()
        if (
                sale_order.team_id
                and sale_order.team_id.beezup_add_delivery_cost):
            sale_order.set_delivery_line()
            delivery_line = sale_order.order_line.filtered(
                lambda ol: ol.is_delivery)
            if len(delivery_line) == 1:
                delivery_line.discount = 100
            else:
                msg = _('Shipping costs could not be added')
                sale_order.message_post(body=msg)
        if bz_order['order_Shipping_Price']:
            shipping_line_data = self.get_shipping_line_data(
                sale_order.id,
                bz_order['order_Shipping_Price'], fiscal_position)
            self._create_with_onchange(line_obj, shipping_line_data)
        else:
            msg = _('Sale order whitout shipping price in Beezup')
            sale_order.message_post(body=msg)
        return log

    def create_beezup_sale_order(self, bz_order):
        res_dict = {'errors': []}
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
            res_dict['errors'].append(
                _('Any item in order \'%s\' has not price') % bz_order_id)
            return res_dict
        if not partner:
            partner = self.create_beezup_partner(bz_order)
        shipping_address = bz_order.get(
            'order_Shipping_AddressLine1',
            bz_order.get('order_Shipping_AddressLine2', bz_order.get(
                'order_Shipping_AddressLine3', False)))
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
        else:
            partner_shipping = partner
        fiscal_position = self.get_fiscal_position(
            bz_order, partner_shipping.zip_id)
        country_iso_code = self.get_country_iso_code(bz_order)
        if not fiscal_position:
            res_dict['errors'].append(_(
                'Fiscal position not found for order \'%s\', '
                'country ISO: \'%s\'') % (bz_order_id, country_iso_code))
            return res_dict
        crm_team_obj = self.env['crm.team']
        crm_team = crm_team_obj.search([
            ('name', '=', bz_order['marketplaceBusinessCode']),
        ], limit=1)
        crm_team_partner_id = (
            crm_team and crm_team.partner_id and crm_team.partner_id.id
            or False)
        if not crm_team:
            crm_team = crm_team_obj.create({
                'name': bz_order['marketplaceBusinessCode'],
            })
        company = self.env.user.company_id
        carrier_id = (
            bz_order.get('order_Shipping_Method', False)
            and self.env['delivery.carrier'].search([
                ('name', '=', bz_order['order_Shipping_Method']),
            ], limit=1).id
            or crm_team.beezup_default_carrier_id.id)
        order_data = {
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
                and company.beezup_parent_partner_id.id or crm_team_partner_id
                or partner_shipping.id),
            'partner_shipping_id': partner_shipping.id or partner.id,
            'from_import_sale_beezup': True,
            'fiscal_position_id': fiscal_position.id,
        }
        if company.sale_number_overwrite:
            order_data['name'] = '%s%s' % (
                crm_team.beezup_prefix_sale_name or '', bz_order_id)
        sale_order = self.env['sale.order'].create(order_data)
        product_log = self.create_order_lines(
            bz_order, sale_order, fiscal_position)
        res_dict['errors'] += product_log
        _log.info('Beezup sale order %s created' % sale_order.id)
        res_dict['order'] = sale_order
        confirm_errors = self.confirm_sale_order(bz_order, sale_order)
        if confirm_errors:
            res_dict['errors'] += confirm_errors
        process_errors = self.process_order(bz_order, sale_order)
        if process_errors:
            res_dict['errors'] += process_errors
        return res_dict

    def confirm_sale_order(self, bz_order, sale_order):
        errors = []
        invoice_policy = list(set(sale_order.order_line.filtered(
            lambda ln: ln.product_id.type != 'service').mapped(
            'product_id.invoice_policy')))
        if invoice_policy != ['order']:
            msg_error = _(
                'The invoice policy of the products of order with origin '
                '\'%s\' is %s and is not contemplated. It must be \'order\''
                ', so the pickings and the invoice has not been created; check'
                ' manually.') % (sale_order.origin, invoice_policy)
            errors.append(msg_error)
            _log.warn(msg_error)
            return errors
        sale_order.action_confirm()
        sale_order.action_invoice_create()
        invoices = sale_order.invoice_ids
        if not invoices:
            msg_error = (_(
                'The order with origin \'%s\' has not generated invoice; '
                'check manually.') % sale_order.origin)
            errors.append(msg_error)
            _log.warn(msg_error)
            return errors
        if len(invoices) > 1:
            msg_error = (_(
                'More than one invoice has been generated from the order with '
                'origin \'%s\'; check manually.') % sale_order.origin)
            errors.append(msg_error)
            _log.warn(msg_error)
            return errors
        invoice = invoices[0]
        invoice.action_invoice_open()
        if invoice.state != 'open':
            msg_error = (_(
                'The invoice associated with the order with origin \'%s\' has '
                'not been opened correctly, check manually.') % (
                    sale_order.origin))
            errors.append(msg_error)
            _log.warn(msg_error)
            return errors
        payment_date = (
            bz_order.get('order_PayingUtcDate')
            and datetime.strptime(
                bz_order['order_PayingUtcDate'], '%Y-%m-%dT%H:%M:%SZ')
            or False)
        company = self.env.user.company_id
        bz_payment_method = bz_order.get('order_PaymentMethod')
        journal_payment_id = company.beezup_journal_payment_id
        if sale_order.team_id:
            team = sale_order.team_id
            if 'import_payment_journal_id' in team._fields.keys():
                journal_payment_id = team.import_payment_journal_id
        self.register_payment(
            bz_payment_method, invoice, journal_payment_id, payment_date)
        if invoice.state != 'paid':
            msg_error = (_(
                'The invoice associated with the order with origin \'%s\' has '
                'not been paid correctly, check manually.') % sale_order.origin)
            errors.append(msg_error)
            _log.warn(msg_error)
        if bz_order.get('order_PurchaseUtcDate'):
            invoice.date_invoice = datetime.strptime(
                bz_order['order_PurchaseUtcDate'], '%Y-%m-%dT%H:%M:%SZ').date()
        return errors

    def create_sale_order(self, bz_order, error_dict):
        bz_order_id = bz_order['order_MarketplaceOrderId']
        sale_orders = self.env['sale.order'].search([
            '|',
            ('name', 'ilike', bz_order_id),
            ('origin', 'ilike', bz_order_id),
        ])
        if len(sale_orders) > 1:
            msg_error = (_(
                'More than one sale order with origin \'%s\' '
                'has been found. The order details could not be '
                'updated.') % bz_order_id)
            _log.warn(msg_error)
            error_dict['skip_count'] += 1
            return error_dict
        elif not sale_orders:
            bz_status = (
                bz_order['order_Status_BeezUPOrderStatus'].upper())
            order_bz_status = self.get_beezup_statuses().get(bz_status)
            if order_bz_status == 'new':
                msg_error = (_(
                    'Sale order \'%s\' in progress, not imported') % (
                        bz_order_id))
                _log.warn(msg_error)
                error_dict['skip_count'] += 1
                return error_dict
            if order_bz_status == 'cancelled':
                msg_error = (_(
                    'Sale order \'%s\' cancelled, not imported') % (
                        bz_order_id))
                _log.warn(msg_error)
                error_dict['skip_count'] += 1
                return error_dict
            errors = self.check_required_order_data(bz_order)
            if errors:
                msg_error = (_(
                    'Sale order \'%s\' has not required fields: %s') % (
                        bz_order_id, ', '.join(errors)))
                error_dict['errors'].append(msg_error)
                _log.error(msg_error)
                error_dict['error_count'] += 1
                return error_dict
            sale_orders_data = self.create_beezup_sale_order(bz_order)
            sale_orders = sale_orders_data.get('order')
            errors_sale_order = sale_orders_data.get('errors')
            if not sale_orders:
                if errors_sale_order:
                    error_dict['errors'] += (errors_sale_order)
                return error_dict
            file_json_content = json.dumps(bz_order, indent=4, sort_keys=True)
            self.env['ir.attachment'].create({
                'name': 'BEEZUP_JSON_%s' % sale_orders.name,
                'datas': base64.b64encode(file_json_content.encode()),
                'datas_fname': 'beezup_json_%s.json' % sale_orders.name,
                'res_model': 'sale.order',
                'res_id': sale_orders.id,
                'mimetype': 'application/json',
            })
            if sale_orders and errors_sale_order:
                sale_orders.message_post(body=errors_sale_order)
        else:
            bz_status = (
                bz_order['order_Status_BeezUPOrderStatus'].upper())
            if (sale_orders.etag_beezup == bz_order['etag']
                    or bz_status == sale_orders.state_beezup):
                _log.info('No changes in \'%s\', skiped' % bz_order_id)
                return error_dict
            process_errors = self.process_order(bz_order, sale_orders)
            if process_errors:
                error_dict['errors'] += process_errors
                error_dict['skip_count'] += 1
                return error_dict

    def import_beezup_orders(self):
        error_dict = {
            'errors': [],
            'error_count': 0,
            'skip_count': 0,
        }
        company = self.env.user.company_id
        beezup_data = self.get_beezup_order_data()
        if not beezup_data:
            return False
        errors = beezup_data.get('errors')
        if errors:
            error_dict['errors'] += errors
            return error_dict
        beezup_orders = beezup_data.get('orders')
        _log.info('%s Beezup orders will be imported' % len(beezup_orders))
        crm_team_obj = self.env['crm.team']
        for order_count, bz_order in enumerate(beezup_orders):
            bz_order_id = bz_order['order_MarketplaceOrderId']
            _log.info('%s/%s %s' % (
                order_count + 1, len(beezup_orders), bz_order_id))
            crm_team = crm_team_obj.search([
                ('name', '=', bz_order['marketplaceBusinessCode']),
            ], limit=1)
            if crm_team:
                order_datetime = datetime.strptime(
                    bz_order['order_PurchaseUtcDate'], '%Y-%m-%dT%H:%M:%SZ')
                if (crm_team.avoid_beezup_sync
                        or crm_team.beezup_sync_date_start
                        and crm_team.beezup_sync_date_start > order_datetime):
                    error_dict['skip_count'] += 1
                    _log.info('Sale marked as not importable in sales team %s, '
                              'order %s skipped' % (crm_team.name, bz_order_id))
                    continue
            if bz_order.get('processing', False):
                error_dict['skip_count'] += 1
                _log.info('%s Beezup order procesing' % bz_order_id)
                continue
            self.savepoint('import_beezup_order')
            done = False
            attempts = 0
            while not done and attempts < 2:
                try:
                    sale_error_dict = self.create_sale_order(
                        bz_order, error_dict)
                    done = True
                except Exception as e:
                    self.rollback('import_beezup_order')
                    attempts += 1
                    if (attempts == 2 and not done
                            and 'concurrent update' not in e.name):
                        error_dict = done and sale_error_dict or error_dict
                        msg_error = _(
                            'Unable to create order %s: %s') % (bz_order_id, e)
                        _log.warn(msg_error)
                        error_dict['errors'].append(msg_error)
                        error_dict['error_count'] += 1
            self.release('import_beezup_order')
        company.beezup_last_sync = datetime.now()
        _log.info('Beezup import complete, %s errors, %s skiped' % (
            error_dict['error_count'], error_dict['skip_count']))
        if error_dict.get('errors', False):
            exeption_line_model_id = self.env['ir.model']._get(
                'base.manage.exception.line').id
            mail_activity_obj = self.env['mail.activity']
            for error in error_dict['errors']:
                error_found = mail_activity_obj.search([
                    ('res_model_id', '=', exeption_line_model_id),
                    ('summary', '=', error)
                ], limit=1)
                if error_found:
                    error_dict['errors'].remove(error)
        return error_dict

    def sync_beezup_orders_state(self):
        error_dict = {'errors': []}
        error_count = 0
        orders_done = self.env['sale.order'].search([
            ('state', '=', 'sale'),
            ('from_import_sale_beezup', '=', True),
            ('create_date', '>', (datetime.now() - timedelta(days=31))),
        ])
        for order_count, order in enumerate(orders_done):
            _log.info('%s/%s %s' % (
                order_count + 1, len(orders_done), order.origin))
            orders_data = self.get_beezup_order_data(order)
            if not orders_data:
                msg_error = _(
                    'Sync with Beezup not possible, order not found for %s' %
                    order.name)
                error_dict['errors'].append(msg_error)
                error_count += 1
                continue
            order_errors = orders_data.get('errors')
            orders = orders_data.get('orders')
            if order_errors:
                error_dict['errors'] += order_errors
                error_count += 1
                continue
            elif len(orders) > 1:
                msg_error = _(
                    'Sync with Beezup not possible, more tan one order found '
                    'for %s' % order.name)
                error_dict['errors'].append(msg_error)
                error_count += 1
                continue
            else:
                bz_status = (
                    orders[0]['order_Status_BeezUPOrderStatus'].upper())
                order_bz_status = self.get_beezup_statuses().get(bz_status)
                if not order_bz_status:
                    msg_error = _(
                        'Unrecognized Beezup status: %s' % (
                            orders[0]['order_Status_BeezUPOrderStatus']))
                    continue
                if (
                        orders[0]['etag'] == order.etag_beezup
                        and order.state_beezup == order_bz_status.upper()
                ):
                    continue
                errors = self.check_required_order_data(orders[0])
                if errors:
                    msg_error = _(
                        'Sale order %s has not required fields: %s' % (
                            orders[0]['order_MarketplaceOrderId'],
                            ', '.join(errors)))
                    error_dict['errors'].append(msg_error)
                    _log.error(msg_error)
                    error_count += 1
                    continue
                self.process_order(orders[0], order)
        _log.info('Beezup sync complete, %s errors' % error_count)
        return error_dict
