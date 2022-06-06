###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import gzip
import itertools
import logging

from odoo import _, api, exceptions, fields, models

try:
    from sp_api.base import Marketplaces, SellingApiBadRequestException
    from sp_api.api import Orders, MerchantFulfillment
except ImportError:
    pass

_log = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('amazon', 'Amazon')],
    )
    amazon_client_id = fields.Char(
        string='Client ID',
    )
    amazon_client_secret = fields.Char(
        string='Client secret',
    )
    amazon_refresh_token = fields.Char(
        string='Refresh token',
    )
    amazon_access_key = fields.Char(
        string='Access key',
    )
    amazon_secret_key = fields.Char(
        string='Secret key',
    )
    amazon_role_arn = fields.Char(
        string='Role ARN',
    )
    amazon_service_shipment = fields.Char(
        string='Shipment Service',
        help='The name of the Amazon service, must be the name of the carrier '
             'and you can put several separated by commas.',
    )
    amazon_service_package_max = fields.Char(
        string='Package max dimension',
        help='The dimension package (width, height, lenght) separated by '
             'comma. The order of dimension not is important',
    )
    amazon_service_label_format = fields.Selection(
        selection=[
            ('PNG', 'PNG'),
            ('PDF', 'PDF'),
            ('ShippingServiceDefault', 'Shipping service default'),
            ('ZPL300', 'ZPL300'),
            ('ZPL203', 'ZPL203'),
        ],
        default='ShippingServiceDefault',
        string='Service label format',
    )
    amazon_region_id = fields.Many2one(
        comodel_name='res.country',
        string='Region',
    )

    @api.constrains('amazon_service_package_max')
    def _check_amazon_service_package_max(self):
        for carrier in self:
            if not carrier.amazon_service_package_max:
                continue
            try:
                dim = carrier.amazon_service_package_max.split(',')
                dim = [float(d) for d in dim]
                if len(dim) != 3:
                    raise Exception()
            except Exception:
                raise exceptions.ValidationError(_(
                    'Amazon package max dimension must be 3 numbers '
                    'separated by comma.'))

    def _amazon_credentials_get(self):
        return dict(
            refresh_token=self.amazon_refresh_token,
            lwa_app_id=self.amazon_client_id,
            lwa_client_secret=self.amazon_client_secret,
            aws_secret_key=self.amazon_secret_key,
            aws_access_key=self.amazon_access_key,
            role_arn=self.amazon_role_arn,
        )

    def _amazon_marketplaces_get(self):
        return Marketplaces[self.amazon_region_id.code.upper()]

    def _amazon_order_id_get(self, picking):
        sale = picking.sale_id
        return sale.client_order_ref and sale.client_order_ref or sale.name

    def _amazon_create_create_shipment(self, picking, item_list, dimension):
        order_id = self._amazon_order_id_get(picking)
        merchant_client = MerchantFulfillment(
            marketplace=self._amazon_marketplaces_get(),
            credentials=self._amazon_credentials_get())
        data = {
            'AmazonOrderId': order_id,
            'ItemList': item_list,
            'ShipFromAddress': {
                'Name': picking.company_id.name,
                'AddressLine1': picking.company_id.street,
                'AddressLine2': picking.company_id.street2,
                'City': picking.company_id.city,
                'CountryCode': picking.company_id.country_id.code,
                'PostalCode': picking.company_id.zip,
                'Phone': picking.company_id.phone,
                'Email': picking.company_id.email,
            },
            'PackageDimensions': {
                'Length': dimension[0],
                'Width': dimension[1],
                'Height': dimension[2],
                'Unit': 'centimeters'
            },
            'Weight': {
                'Value': picking.weight,
                'Unit': picking.weight_uom_id.name,
            },
            'ShippingServiceOptions': {
                'DeliveryExperience': 'DeliveryConfirmationWithoutSignature',
                'LabelFormat': self.amazon_service_label_format,
            }
        }
        try:
            services = merchant_client.get_eligible_shipment_services(data)
        except SellingApiBadRequestException as ex:
            _log.error(data)
            _log.error(ex)
            raise exceptions.ValidationError(
                'Amazon error: %s' % ex.error[0]['message'])
        services_ok = [
            s.strip().upper() for s in self.amazon_service_shipment.split(',')]
        service = None
        for item in services.payload['ShippingServiceList']:
            if item['ShippingServiceName'].upper() in services_ok:
                service = item
                break
        if not service:
            amazon_services = ','.join([
                s['ShippingServiceName']
                for s in services.payload['ShippingServiceList']])
            raise exceptions.ValidationError(_(
                'There is no valid service for this carrier and this order.\n'
                'The services available from Amazon are: %s\n'
                'But only these are allowed by the configuration: %s' % (
                    amazon_services, self.amazon_service_shipment)))
        shipment = merchant_client.create_shipment(
            shipment_request_details=data,
            shipping_service_id=service['ShippingServiceId'],
            ShippingServiceOfferId=service['ShippingServiceOfferId'],
        )
        label = base64.b64decode(
            shipment.payload['Label']['FileContents']['Contents'])
        label = gzip.decompress(label)
        self.env['ir.attachment'].create({
            'name': 'Amazon %s' % shipment.payload['ShipmentId'],
            'datas': base64.b64encode(label),
            'datas_fname': 'amazon_%s' % shipment.payload['ShipmentId'],
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'mimetype': shipment.payload['Label']['FileContents']['FileType'],
        })
        picking.amazon_shipment_id = '%s\n%s' % (
            picking.amazon_shipment_id or '',
            shipment.payload['ShipmentId'])
        return shipment.payload

    def amazon_send_shipping(self, pickings):
        return [self._amazon_send_shipping(p) for p in pickings]

    def amazon_product_get(self, sku):
        product = self.env['product.product'].search(
            [('default_code', '=', sku)], limit=1)
        if not product:
            supplierinfo = self.env['product.supplierinfo'].search(
                [('product_code', '=', sku)], limit=1)
            if supplierinfo:
                product = (
                    supplierinfo.product_id
                    and supplierinfo.product_id
                    or supplierinfo.product_tmpl_id.product_variant_id)
        return product

    def _amazon_send_shipping(self, picking):
        def packaging_get(package, products, res=None):
            if not res:
                res = []
            if not products:
                return res
            for k in products.keys():
                products[k].sort()
            package.sort()
            keys = list(products.keys())
            combinations = []
            for lenght in range(0, len(keys) + 1):
                for subset in itertools.combinations(keys, lenght):
                    if not subset:
                        continue
                    combinations.append(subset)
            packaging = []
            for keys in combinations:
                dim = [0, 0, 0]
                for key in keys:
                    dim[0] += products[key][0]
                    dim[1] = max(dim[1], products[key][1])
                    dim[2] = max(dim[2], products[key][2])
                if all(package[x] >= dim[x] for x in range(3)):
                    packaging.append([keys, dim])
            if not packaging:
                return []
            best_combination, dimension = packaging.pop()
            res.append([best_combination, dimension])
            for key in best_combination:
                del(products[key])
            return packaging_get(package, products, res)

        self.ensure_one()
        order_client = Orders(
            marketplace=self._amazon_marketplaces_get(),
            credentials=self._amazon_credentials_get())
        order_id = self._amazon_order_id_get(picking)
        try:
            order_items = order_client.get_order_items(order_id)
        except SellingApiBadRequestException as ex:
            if ex.error[0]['code'] == 'InvalidInput':
                raise exceptions.ValidationError(
                    _('Order Id %s not exists in Amazon, please change client '
                      'ref in sale order with a valid Amazon Order Id') % (
                        order_id))
            raise exceptions.ValidationError(ex.error[0]['message'])
        products = {}
        for move in picking.move_ids_without_package:
            products.setdefault(move.product_id, 0)
            products[move.product_id] += move.quantity_done
        items = {}
        for item in order_items.payload['OrderItems']:
            product = self.amazon_product_get(item['SellerSKU'])
            if not product:
                raise exceptions.ValidationError(
                    'Product Amazon SKU %s not exists!' % item['SellerSKU'])
            if product not in products:
                continue
            for index in range(int(products[product])):
                key = '%s::%s' % (item['OrderItemId'], index)
                items[key] = {
                    'product': product,
                    'item': item,
                    'dimension': [
                        product.product_length,
                        product.product_height,
                        product.product_width,
                    ],
                }
        package_max = self.amazon_service_package_max.split(',')
        package_max = [float(d) for d in package_max]
        packaging = packaging_get(
            package_max,
            {k: v['dimension'] for k, v in items.items()})
        item_lists = []
        dimensions = []

        def join_items(package):
            res = {}
            for key in package:
                res.setdefault(items[key]['item']['OrderItemId'], 0)
                res[items[key]['item']['OrderItemId']] += 1
            return res

        for package, dimension in packaging:
            item_lists.append([
                {
                    'OrderItemId': items['%s::0' % key]['item']['OrderItemId'],
                    'Quantity': qty,
                } for key, qty in join_items(package).items()
            ])
            dimensions.append(dimension)
        if not item_lists:
            raise exceptions.ValidationError(_(
                'Without packages, I can not continue for security'))
        res = {
            'tracking_number': '',
            'exact_price': 0,
        }
        for index in range(len(item_lists)):
            payload = self._amazon_create_create_shipment(
                picking, item_lists[index], dimensions[index])
            res['tracking_number'] = payload['TrackingId']
            res['exact_price'] += payload['ShippingService']['Rate']['Amount']
        return res

    def amazon_cancel_shipment(self, picking):
        merchant_client = MerchantFulfillment(
            marketplace=self._amazon_marketplaces_get(),
            credentials=self._amazon_credentials_get())
        shipment_ids = (picking.amazon_shipment_id or '').split('\n')
        for shipment_id in [s for s in shipment_ids if s]:
            res = merchant_client.cancel_shipment(shipment_id)
        picking.amazon_shipment_id = False
        return res

    def amazon_tracking_state_update(self, picking):
        raise NotImplementedError(_('''
            Amazon doesn't provide methods to tracking
        '''))

    def amazon_get_tracking_link(self, picking):
        raise NotImplementedError(_('''
            Amazon doesn't provide methods to tracking
        '''))

    def amazon_rate_shipment(self, order):
        raise NotImplementedError(_('''
            Amazon doesn't provide methods to compute delivery
            rates, so you should relay on another price method instead or
            override this one in your custom code.
        '''))
