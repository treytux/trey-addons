###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import _, api, exceptions, fields, models
from odoo.tools.float_utils import float_compare

_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'website.woo.mixin']

    def woo_sync_export_records(self, website, products=None):
        pass

    def woo_upload(self, website, update_fields=None):
        pass

    @api.model
    def woo_delete(self, website, woo_ids=None):
        return False

    def _woo_rpc_upload(self, data):
        pass

    def woo_endpoint_get(self, woo_id=None):
        endpoint = 'orders'
        if woo_id:
            endpoint = '%s/%s' % (endpoint, woo_id)
        return endpoint

    def woo_partner_browse_or_create(
            self, website, data, meta_data=None, parent=None,
            partner_type=False, fiscal_position_id=False):
        if not meta_data:
            meta_data = {}
        partner_obj = self.env['res.partner']
        partner = None
        partner_name = ' '.join([data['first_name'], data['last_name']])
        if partner_type == 'delivery' and data['company']:
            partner_name = '%s (%s)' % (data['company'], partner_name)
        vat = meta_data.get(
            'yweu_billing_vat', meta_data.get('_billing_yweu_vat', False))
        if vat:
            vat = ''.join(c for c in vat if c.isalnum()).upper()
        if vat:
            country_iso = meta_data.get('ywev_COUNTRY', '')
            if country_iso and not vat.startswith(country_iso):
                vat = ''.join([country_iso, vat]).upper()
            if partner_type != 'delivery':
                partner = partner_obj.search([('vat', '=', vat)], limit=1)
        if not partner and partner_type != 'delivery' and 'email' in data:
            partner = partner_obj.search([
                ('type', '!=', 'delivery'),
                ('email', 'ilike', data['email']),
            ], limit=1)
        if not partner:
            if parent:
                partner = partner_obj.search([
                    ('parent_id', '=', parent.id),
                    ('street', '=', data['address_1']),
                    ('street2', '=', data['address_2']),
                    ('phone', '=', data['phone']),
                ], limit=1)
            else:
                partner = partner_obj.search([
                    ('name', '=', partner_name),
                    ('street', '=', data['address_1']),
                    ('street2', '=', data['address_2']),
                    ('phone', '=', data['phone']),
                ], limit=1)
        partner_data = {
            'type': partner_type,
            'company_id': website.company_id.id,
            'parent_id': parent and parent.id or None,
            'name': partner_name,
            'comercial': data.get('company'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'street': data['address_1'],
            'street2': data['address_2'],
            'vat': vat,
            'property_account_position_id': fiscal_position_id,
        }
        if partner_type == 'delivery':
            del partner_data['vat']
        zip_ids = self.env['res.city.zip'].search([
            ('name', '=', data['postcode']),
        ], limit=1)
        if zip_ids:
            zip_data = {
                'zip_id': zip_ids[0].id,
                'city': zip_ids[0].city_id.name,
                'city_id': zip_ids[0].city_id.id,
                'state_id': zip_ids[0].city_id.state_id.id,
                'country_id': zip_ids[0].city_id.country_id.id,
            }
            if len(zip_ids) > 1:
                zip_data.update({
                    'zip_id': False,
                    'city': data['city'],
                    'city_id': False,
                    'zip': data['postcode'],
                })
            partner_data.update(zip_data)
        elif data['country']:
            country = self.env['res.country'].search([
                ('code', 'ilike', data['country']),
            ])
            partner_data.update({
                'country_id': country.id,
                'city': data['city'],
                'zip': data['postcode'],
            })
            if data.get('state'):
                partner_data['city'] = '%s (%s)' % (
                    data['city'], data['state'])
        if partner:
            has_email = (
                data.get('email') and partner.email
                and data['email'] not in partner.email)
            if has_email:
                partner_data['email'] = ';'.join(
                    [partner.email, partner_data['email']])
            else:
                del partner_data['email']
            partner.write(partner_data)
        else:
            partner = partner_obj.create(partner_data)
        if hasattr(partner, '_onchange_zip_id'):
            partner._onchange_zip_id()
        if partner.city:
            return partner
        partner.write({
            'city': data['city'],
            'zip': data['postcode'],
        })
        state = self.env['res.country.state'].search([
            ('name', '=', data['state']),
        ], limit=1)
        if state:
            partner.write({
                'state_id': state.id,
                'country_id': state.country_id.id,
            })
            return partner
        country = self.env['res.country'].search([
            ('code', '=', data['country']),
        ])
        if country:
            partner.write({
                'city': '%s (%s)' % (partner.city, data['state']),
                'country_id': state.country_id.id,
            })
            return partner
        partner.write({
            'city': '%s (%s) - %s' % (
                partner.city, data['state'], data['country']),
            'country_id': state.country_id.id,
        })
        return partner

    def woo_sync_import_record(self, website, data, refunds=None):
        self = self.with_context(website=website)
        product_obj = self.env['product.product']

        def product_search(product_id=None, default_code=None):
            product = product_obj.browse()
            if product_id:
                product = product_obj.woo_search_id(product_id)
            if not product and default_code:
                product = product_obj.search([
                    ('default_code', '=', default_code),
                ], limit=1)
            return product

        meta_data = {item['key']: item['value'] for item in data['meta_data']}
        taxes_ids = [t['rate_id'] for t in data['tax_lines']]
        taxes = self.env['website.woo.mapp.tax'].search([
            ('website_id', '=', website.id),
            ('woo_id', 'in', taxes_ids),
        ])
        taxes = {t.woo_id: t for t in taxes}
        if len(taxes) != len(taxes_ids):
            not_found = []
            tax_total = 0
            for tax in data['tax_lines']:
                if tax['rate_id'] not in taxes:
                    not_found.append(tax['label'])
                    tax_total += float(tax['tax_total'])
            if tax_total:
                raise exceptions.UserError(
                    'Taxs not mapped:\n'
                    '%s\n\n'
                    'Please launch a sync operation and mapp this taxes'
                    'before continue.' % '\n'.join(not_found))
        if not all([t.tax_id for t in taxes.values()]):
            not_found = [t.name for t in taxes.values() if not t.tax_id]
            raise exceptions.UserError(
                'Taxs not mapped:\n'
                '%s\n\n'
                'Please go to Website / WooCommerce Tax Mapp for mapp these '
                'taxes.' % '\n'.join(not_found))
        fiscal_position_id = False
        if taxes:
            tax = list(taxes.values())[0]
            if meta_data.get('is_vat_exempt') == 'yes':
                fiscal_position_id = tax.intracommunity_fiscal_position_id.id
            else:
                fiscal_position_id = tax.fiscal_position_id.id

        def taxes_get(woo_ids):
            vies = meta_data.get('is_vat_exempt') == 'yes'
            tax_ids = []
            for id in woo_ids:
                if id not in taxes:
                    continue
                tax_ids.append(
                    taxes[id].intracommunity_tax_id.id
                    if vies else taxes[id].tax_id.id)
            return [(6, 0, tax_ids)]

        errors = []
        partner = self.woo_partner_browse_or_create(
            website, data['billing'], meta_data,
            fiscal_position_id=fiscal_position_id)
        if 'partner_email_unique' not in self.env.registry._init_modules:
            data['shipping']['email'] = data['billing']['email']
        partner_shipping = self.woo_partner_browse_or_create(
            website, data['shipping'], meta_data, partner,
            partner_type='delivery')
        sale_data = {
            'name': data['number'],
            'website_id': website.id,
            'company_id': website.company_id.id,
            'date_order': self.woo_format_str_to_date(
                data['date_created_gmt']),
            'team_id': website.salesteam_id.id,
            'user_id': website.salesperson_id.id,
            'partner_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
            'note': data['customer_note'],
            'fiscal_position_id': fiscal_position_id,
        }
        sale = self.woo_search_id(data['id'])
        if not sale:
            sale = self.create(sale_data)
        else:
            sale.order_line.unlink()
            sale.write(sale_data)
        uom = self.env.ref('uom.product_uom_unit')
        product_concept = self.env.ref('woocommerce_connector.product_concept')
        sale_line_obj = self.env['sale.order.line']
        for item in data['line_items']:
            name = item['name']
            product = product_search(item['product_id'], item['sku'])
            if not product:
                errors.append(_('Product <b>%s</b> not exist (SKU: %s)') % (
                    item['name'], item.get('sku') or ''))
                product = product_concept
                name = '[%s] %s' % (item['sku'], name)
            line = sale_line_obj.create({
                'order_id': sale.id,
                'product_id': product.id,
                'name': name,
                'product_uom_qty': item['quantity'],
                'product_uom': product and product.uom_id.id or uom.id,
                'price_unit': item['price'],
                'tax_id': taxes_get([it['id'] for it in item['taxes']]),
            })
            if line.price_unit != item['price']:
                line.write({'price_unit': item['price']})
            if float(item['subtotal']) != line.price_subtotal:
                errors.append(_(
                    'The order line with the product <b>%s</b> has a '
                    'different subtotal, %s per unit for %s quantity has a '
                    'result of %s, WooCommerce says that this result is '
                    '%s.') % (
                        line.name, line.price_unit, line.product_uom_qty,
                        line.price_subtotal, item['subtotal']
                ))
        for item in data['shipping_lines']:
            product = product_search(None, item['method_id'])
            if not product:
                errors.append(
                    _('Product for delivery cost <b>%s</b> not exist '
                      '(SKU: %s)') % (item['method_title'], item['method_id']))
                product = product_concept
            taxs = taxes_get([it['id'] for it in item['taxes']])
            if not item['taxes']:
                taxs = [(6, 0, sale.order_line[0].tax_id.ids)]
            sale_line_obj.create({
                'is_delivery': True,
                'order_id': sale.id,
                'product_id': product.id,
                'name': item['method_title'],
                'product_uom_qty': 1,
                'product_uom': product and product.uom_id.id or uom.id,
                'price_unit': item['total'],
                'tax_id': taxs,
            })
        for item in data['fee_lines']:
            product = product_obj.search([('name', '=', item['name'])])
            if not product:
                errors.append(_(
                    'Product for fee cost <b>%s</b> not exist, please create a '
                    'product with the same name') % (
                        item['name'], item['method_id']))
                product = product_concept
            sale_line_obj.create({
                'order_id': sale.id,
                'product_id': product.id,
                'name': item['name'],
                'product_uom_qty': 1,
                'product_uom': product and product.uom_id.id or uom.id,
                'price_unit': item['amount'],
                'tax_id': taxes_get([it['id'] for it in item['taxes']]),
            })
        info = [
            'IP address: %s' % data['customer_ip_address'],
            'User Agent: %s' % data['customer_user_agent'],
        ]
        total = float(data['total'])
        if data['refunds']:
            if not refunds:
                refunds = self.env['sale.order'].woo_rpc_call(
                    'get', 'orders/%s/refunds' % data['number'],
                    {'params': {}}, website=website)
            for refund in refunds:
                reason = ''
                total -= float(refund['amount'])
                if not refund['line_items'] \
                   and not refund['shipping_lines'] \
                   and refund['reason']:
                    info.append('Refund: %s' % refund['reason'])
                for item in refund['line_items']:
                    reason = (
                        '"%s"' % refund['reason'] if refund['reason'] else '')
                    lines = sale.order_line.filtered(
                        lambda ln:
                            ln.product_id.default_code == item['sku']
                            or ln.name.startswith('[%s] ' % item['sku']))
                    quantity = float(item['quantity'])
                    if quantity < 0:
                        lines.name += (_('\\nRefund %s of %s quantities') % (
                            reason, item['quantity']))
                        lines.product_uom_qty += quantity
                        # price_unit is precomputed from product+uom+qty,
                        # restore the order price after qty change
                        lines.price_unit = float(item['price'])
                        continue
                    subtotal = float(item['subtotal'])
                    if subtotal < 0:
                        lines.price_unit += round(
                            subtotal / max(1, lines.product_uom_qty), 2)
                        lines.name += (_('\nRefund %s of %s untaxed price') % (
                            reason, item['subtotal']))
                for item in refund['shipping_lines']:
                    lines = sale.order_line.filtered(
                        lambda ln:
                            ln.product_id.default_code == item['method_id'])
                    lines.price_unit += float(item['total'])
                    lines.name += (_('\nRefund %s of %s untaxed price') % (
                        reason, item['total']))
        for coupon in data['coupon_lines']:
            try:
                if isinstance(coupon, str):
                    description = coupon
                else:
                    meta = coupon.get('meta_data', [{}])
                    description = (
                        meta[0].get('display_value', {})
                        .get('description', '')
                        if isinstance(meta[0], dict) else ''
                    )
            except Exception as ex:
                description = ''
                _log.error('Error obtaining sale %s coupon description: %s',
                           data['number'], ex)
            coupon_code = (
                coupon.get('code', '') if isinstance(coupon, dict) else coupon)
            sale_line_obj.create({
                'order_id': sale.id,
                'display_type': 'line_note',
                'name': '\n'.join([
                    coupon_code,
                    description,
                ]),
            })
        payment = self.env['payment.provider'].search([
            ('name', '=', data['payment_method_title']),
            '|',
            ('website_id', '=', website.id),
            ('website_id', '=', False),
        ], limit=1)
        if not payment:
            errors.append(_('Payment method <b>%s</b> not exist.') % (
                data['payment_method_title']))
        else:
            self.env['payment.transaction'].create({
                'sale_order_ids': [(6, 0, sale.ids)],
                'amount': sale.amount_total,
                'provider_id': payment.id,
                'operation': 'validation',
                'currency_id': self.env.user.company_id.currency_id.id,
                'reference': sale.name,
                'partner_id': self.partner_id.id,
            })
            sale.payment_mode_id = payment.payment_mode_id.id
        body = _('Import from WooCommerce <b>%s</b>') % website.name
        body += ''.join(['<ul>%s</ul>' % ln for ln in info])
        sale.message_post(body=body)
        total = round(total, 2)
        if float_compare(total, sale.amount_total, 2) != 0:
            errors.append(
                _('The amount total is different than in WooCommerce, '
                  '(woocommerce total %s)') % total)
        if not total:
            sale.action_cancel()
        if errors:
            sale.activity_schedule(
                summary=_('Check for errors when importing the order'),
                act_type_xmlid='mail.mail_activity_data_warning',
                user_id=(
                    website.salesperson_id.id
                    if website.salesperson_id else self.env.user.id),
                note='<br/>'.join(errors),
                date_deadline=fields.Date.today())
            body = _(
                'Error when import sale order <b>%s</b> from <b>%s</b>.' % (
                    data['number'], website.name))
            body += ''.join(['<ul>%s</ul>' % ln for ln in errors])
            sale.message_post(body=body)
        return sale
