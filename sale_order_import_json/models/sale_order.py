###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json

from dateutil.relativedelta import relativedelta
from odoo import _, api, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def create_with_onchange(self, record, values):
        onchange_specs = {
            field_name: '1' for field_name, field in record._fields.items()
        }
        data = self._add_missing_default_values({})
        data.update(values)
        new = record.new(data)
        new._origin = None
        res = {'value': {}, 'warnings': set()}
        for field in record._onchange_spec():
            if onchange_specs.get(field):
                new._onchange_eval(field, onchange_specs[field], res)
        cache = record._convert_to_write(new._cache)
        cache.update(values)
        return record.create(cache)

    def check_default_selection_field(self, content, key, record):
        return record._fields[key].default(record._name) if (
            content[key] not in dict(record._fields[key].selection)) else (
            content[key])

    @api.model
    def json_import(self, json_content):

        def clean_content(model, content, ignore=None):
            res = {}
            if ignore is None:
                ignore = []
            for key, value in content.items():
                if key in ignore:
                    continue
                if key not in model._fields:
                    continue
                if not isinstance(value, (int, float, bool, str)):
                    continue
                res[key] = value
            return res

        def partner_get_or_create(data):
            partners = self.env['res.partner'].search([
                ('email', '=', data['email'])])
            if not partners:
                partners = self.env['res.partner'].create(data)
            if len(partners) > 1:
                raise ValidationError(
                    _('Multiple partners with same email "%s"' % (
                        json_content['partner']['email'])))
            return partners

        def partner_shipping_get_or_create(data):
            partners = self.env['res.partner'].search([
                ('name', '=', data['name']),
                ('email', '=', data['email']),
                ('street', '=', data['street']),
                ('street2', '=', data['street2']),
                ('city', '=', data['city']),
                ('phone', '=', data['phone']),
            ])
            if not partners:
                parent = self.env['res.partner'].search([
                    ('email', '=', data['email']),
                ])
                if parent:
                    data.update({
                        'parent_id': parent.id,
                        'email': False,
                        'type': 'delivery',
                    })
                partners = self.env['res.partner'].create(data)
            if len(partners) > 1:
                raise ValidationError(
                    _('Multiple partners shipping "%s" with same info' % (
                        json_content['partner']['email'])))
            return partners

        def get_journal(data):
            journals = self.env['account.journal'].search([
                ('name', '=', data),
            ])
            if not journals:
                raise ValidationError(
                    _('Journal with name "%s" not found' % (data)))
            if len(journals) > 1:
                raise ValidationError(
                    _('Multiple journals with same name "%s"' % (data)))
            return journals

        def get_payment_method(data):
            methods = self.env['account.payment.method'].search([
                '|',
                ('name', '=', data),
                ('code', '=', data),
            ])
            if not methods:
                raise ValidationError(
                    _('Payment method with name "%s" not found' % (data)))
            if len(methods) > 1:
                raise ValidationError(
                    _('Multiple payment method with same name "%s"' % (data)))
            return methods

        def get_crm_team(data):
            teams = self.env['crm.team'].search([
                ('name', '=', data),
            ])
            if not teams:
                raise ValidationError(
                    _('Sales team with name "%s" not found' % (data)))
            if len(teams) > 1:
                raise ValidationError(
                    _('Multiple sales team with same name "%s"' % (data)))
            return teams

        def get_carrier(data):
            carriers = self.env['delivery.carrier'].search([
                ('name', '=', data),
            ])
            if not carriers:
                raise ValidationError(
                    _('Delivery carrier with name "%s" not found' % data))
            if len(carriers) > 1:
                raise ValidationError(
                    _('Multiple carriers with same name "%s"' % data))
            return carriers

        file_json_content = json.dumps(json_content, indent=4, sort_keys=True)
        partner = partner_get_or_create(json_content['partner'])
        json_content['partner_id'] = partner.id
        if json_content.get('partner_shipping', False):
            partner_shipping = partner_shipping_get_or_create(
                json_content['partner_shipping'])
            json_content['partner_shipping_id'] = partner_shipping.id
        data = clean_content(self.env['sale.order'], json_content, ['state'])
        team = False
        if json_content.get('team_name', False):
            team = get_crm_team(json_content['team_name'])
            if 'user_id' not in data and team.user_id:
                data['user_id'] = team.user_id.id
            data.update({
                'team_id': team.id,
            })
        if json_content.get('carrier_id', False):
            carrier = get_carrier(json_content['carrier_id'])
            data.update({
                'carrier_id': carrier.id,
            })
        if 'user_id' not in data:
            login_user = self._context.get('login_user')
            data['user_id'] = login_user and login_user.id or None
        sale = self.create_with_onchange(self, data)
        if json_content.get('warehouse_id', False):
            sale.warehouse_id = json_content['warehouse_id']
        sale.state = self.check_default_selection_field(
            json_content, 'state', sale)
        if json_content.get('date_planned', False):
            user = (
                self.env.context.get('login_user', False)
                or self.env['res.users'].browse(self.env.context.get('uid')))
            sale.date_planned = sale.date_planned - relativedelta(
                hours=int(user.tz_offset[1:3]))
        sale_line_obj = self.env['sale.order.line']
        for line in json_content['order_line']:
            supplierinfo = False
            products = self.env['product.product'].search([
                '|',
                ('default_code', '=', line['default_code']),
                ('barcode', '=', line['default_code']),
            ])
            if not products:
                supplierinfo = self.env['product.supplierinfo'].search([
                    ('product_code', '=', line['default_code'])
                ], limit=1)
                if supplierinfo:
                    products = (
                        supplierinfo.product_id and supplierinfo.product_id
                        or supplierinfo.product_tmpl_id.product_variant_id)
            if not products:
                raise ValidationError(
                    'Product with code %s not exist' % line['default_code'])
            if len(products) > 1:
                raise ValidationError(
                    'Many products with same code %s' % line['default_code'])
            data = clean_content(sale_line_obj, line)
            data.update({
                'order_id': sale.id,
                'product_id': products.id,
                'price_unit': line['price_unit_untaxed'],
            })
            line_total_taxed = (
                float(line['price_unit_taxed']) * float(
                    line['product_uom_qty']))
            line = self.create_with_onchange(sale_line_obj, data)
            if line.discount != 100 and abs(line_total_taxed - (
                    line.price_tax + line.price_subtotal)) > 0.6:
                raise ValidationError(
                    _('Price with taxes does not match '
                      'with calculated by Odoo:\nLine taxes in JSON: %s\n'
                      'Total line taxes calculated by Odoo: %s') % (
                        line_total_taxed,
                        line.price_tax + line.price_subtotal))
            if supplierinfo and 'supplierinfo_id' in sale_line_obj._fields:
                line.write({
                    'supplierinfo_id': supplierinfo.id,
                    'vendor_id': supplierinfo.name.id,
                })
        if not json_content.get('carrier_id', False):
            sale.assign_cheapest_delivery_carrier()
        sale.get_delivery_price()
        self.env['ir.attachment'].create({
            'name': 'JSON_%s' % sale.name,
            'datas': base64.b64encode(file_json_content.encode()),
            'datas_fname': 'json_%s.json' % sale.name,
            'res_model': 'sale.order',
            'res_id': sale.id,
            'mimetype': 'application/json',
        })
        if json_content['state'] in ['confirmed', 'confirmed-no-payment']:
            sale.action_confirm()
            for picking in sale.picking_ids:
                picking.action_confirm()
                picking.action_assign()
            if any(line.qty_to_invoice == 0 for line in sale.order_line):
                raise ValidationError(
                    _('Lines without quantity to be invoiced for order %s' % (
                        json_content['name'])))
            sale.action_invoice_create()
            for invoice in sale.invoice_ids:
                invoice.date_invoice = json_content['invoice_date']
                invoice.action_invoice_open()
                if json_content['state'] == 'confirmed':
                    payment_method = get_payment_method(
                        json_content['payment_method_name'])
                    journal = team and team.import_payment_journal_id or False
                    if json_content.get('payment_journal_name', False):
                        journal = get_journal(
                            json_content['payment_journal_name'])
                    if not journal:
                        raise ValidationError(_(
                            'For payment procces you must pass a '
                            'payment_journal_name params or configure sales '
                            'team'))
                    if journal.type not in ['bank', 'cash']:
                        raise ValidationError(
                            _('The journal "%s" must be the type bank or '
                              'cash') % journal.name)
                    payment = self.env['account.payment'].with_context(
                        active_model='account.invoice',
                        active_id=invoice.id,
                        active_ids=invoice.ids,
                    ).create({
                        'name': sale.name,
                        'payment_method_id': payment_method.id,
                        'journal_id': journal.id,
                        'payment_date': json_content['invoice_date'],
                    })
                    payment.action_validate_invoice_payment()
        return sale.id
