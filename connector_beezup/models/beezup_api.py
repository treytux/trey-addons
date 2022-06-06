###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
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

    def clean_zip(self, zip_value):
        if not isinstance(zip_value, float):
            zip_value = re.sub('[^0-9]', '', str(zip_value))
        return zip_value and int(zip_value) or ''

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
                min_period = datetime.now() - timedelta(days=2)
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
            msg_error = res_dict['errors'][0]['message']
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
            'order_Buyer_AddressCountryIsoCodeAlpha2',
            'order_Buyer_AddressPostalCode',
            'order_MarketplaceOrderId',
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
            order.get('order_Shipping_AddressLine2', None))
        if not shipping_address:
            errors.append('order_Shipping_AddressLine')
        return errors

    def search_fiscal_position(self, country):
        fiscal_positions = self.env['account.fiscal.position'].search([
            ('auto_apply', '=', True),
            ('country_id', '=', country.id),
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
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
            and company.beezup_parent_partner_id.property_account_position_id
            or False)
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
        if order_iso_code.upper() in ['ES', 'ESP']:
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
            'NEW': 'paid',
            'INPROGRESS': 'paid',
            'PENDING': 'paid',
            'TOSHIP': 'paid',
            'SHIPPING': 'paid',
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
                'proccesed') % (order.origin, bz_status))
            return errors
        if order.state_beezup == order_bz_status:
            return errors
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
                        bz_order['order_Shipping_EarliestShipUtcDate'],
                        '%Y-%m-%dT%H:%M:%SZ')
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
        clean_zip = self.clean_zip(bz_order['order_Buyer_AddressPostalCode'])
        order_iso_code = bz_order.get('order_Buyer_AddressCountryIsoCodeAlpha2')
        zip = self.env['res.city.zip'].search([
            ('name', '=', clean_zip),
            ('city_id.country_id.code', '=', order_iso_code.upper()),
        ], limit=1)
        country_id = bz_state_region_id = False
        if not zip:
            country_id = self.env['res.country'].search([
                ('code', '=', bz_order[
                    'order_Buyer_AddressCountryIsoCodeAlpha2']),
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
            'street2': bz_order.get('order_Buyer_AddressLine2'),
            'zip': zip and zip.name or bz_order.get(
                'order_Buyer_AddressPostalCode', ''),
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
            or company.beezup_fiscal_position_id.id)
        return self.env['res.partner'].create(partner_data)

    def create_beezup_partner_shipping(self, bz_order, parent):
        clean_zip = self.clean_zip(bz_order['order_Buyer_AddressPostalCode'])
        order_iso_code = bz_order.get('order_Buyer_AddressCountryIsoCodeAlpha2')
        zip = self.env['res.city.zip'].search([
            ('name', '=', clean_zip),
            ('city_id.country_id.code', '=', order_iso_code.upper()),
        ], limit=1)
        country_id = bz_state_region_id = False
        if not zip:
            country_id = self.env['res.country'].search([
                ('code', '=', bz_order[
                    'order_Buyer_AddressCountryIsoCodeAlpha2']),
            ], limit=1).id
            bz_state_region = bz_order.get(
                'order_Shipping_AddressStateOrRegion', False)
            if bz_state_region:
                bz_state_region_id = self.env['res.country.state'].search([
                    ('name', '=', bz_state_region),
                ], limit=1).id
        street1 = bz_order.get('order_Shipping_AddressLine1', None)
        street2 = bz_order.get('order_Shipping_AddressLine2', None)
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

    def create_order_lines(self, bz_order, sale_order, fiscal_position):
        order_lines = []
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
            bz_order.get('order_Shipping_AddressLine2', False))
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
            res_dict['errors'].append(_(
                'Fiscal position not found for order \'%s\', '
                'country ISO: \'%s\'') % (bz_order_id, bz_order.get(
                    'order_Buyer_AddressCountryIsoCodeAlpha2', '-')))
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
            or company.beezup_carrier_id.id)
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
                or partner.id),
            'partner_shipping_id': (
                partner_shipping and partner_shipping.id or partner.id),
            'from_import_sale_beezup': True,
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
        self.register_payment(
            bz_payment_method, invoice, company.beezup_journal_payment_id,
            payment_date)
        if invoice.state != 'paid':
            msg_error = (_(
                'The invoice associated with the order with origin \'%s\' has '
                'not been paid correctly, check manually.') % sale_order.origin)
            errors.append(msg_error)
            _log.warn(msg_error)
        return errors

    def import_beezup_orders(self):
        error_dict = {'errors': []}
        error_count = 0
        skip_count = 0
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
        for order_count, bz_order in enumerate(beezup_orders):
            bz_order_id = bz_order['order_MarketplaceOrderId']
            _log.info('%s/%s %s' % (
                order_count + 1, len(beezup_orders), bz_order_id))
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
                skip_count += 1
            elif not sale_orders:
                bz_status = bz_order['order_Status_BeezUPOrderStatus'].upper()
                order_bz_status = self.get_beezup_statuses().get(bz_status)
                if order_bz_status == 'cancelled':
                    msg_error = (_(
                        'Sale order \'%s\' cancelled, not imported') % (
                            bz_order_id))
                    error_dict['errors'].append(msg_error)
                    _log.warn(msg_error)
                    skip_count += 1
                    continue
                errors = self.check_required_order_data(bz_order)
                if errors:
                    msg_error = (_(
                        'Sale order \'%s\' has not required fields: %s') % (
                            bz_order_id, ', '.join(errors)))
                    error_dict['errors'].append(msg_error)
                    _log.error(msg_error)
                    error_count += 1
                    continue
                sale_orders_data = self.create_beezup_sale_order(bz_order)
                sale_orders = sale_orders_data.get('order')
                if not sale_orders:
                    errors_sale_order = sale_orders_data.get('errors')
                    if errors_sale_order:
                        error_dict['errors'] += (errors_sale_order)
                    continue
            else:
                if sale_orders.etag_beezup == bz_order['etag']:
                    _log.info(
                        'No changes in \'%s\', skiped' % bz_order_id)
                    continue
                process_errors = self.process_order(bz_order, sale_orders)
                if process_errors:
                    error_dict['errors'] += process_errors
                    skip_count += 1
        company.beezup_last_sync = datetime.now()
        _log.info('Beezup import complete, %s errors, %s skiped' % (
            error_count, skip_count))
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
                        and order.state_beezup == order_bz_status
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
