###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import copy
import json

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    import_by_json = fields.Boolean(
        string='Import by JSON',
        copy=False,
    )

    def create_with_onchange(self, record, values):
        onchange_specs = {
            field_name: '1' for field_name, field in record._fields.items()
        }
        data = record._add_missing_default_values({})
        data.update(values)
        new = record.new(data)
        new._origin = record
        res = {'value': {}, 'warnings': set()}
        for field in record._onchange_spec():
            if onchange_specs.get(field):
                new._onchange_eval(field, onchange_specs[field], res)
                new.update(values)
        cache = record._convert_to_write(new._cache)
        cache.update(values)
        return record.create(cache)

    def check_default_selection_field(self, content, key, record):
        return record._fields[key].default(record._name) if (
            content[key] not in dict(record._fields[key].selection)) else (
            content[key])

    def check_pending_approve(self, sale, data):
        return

    def get_partner_invoice_policy(self, sale, data):
        return

    def check_sale_invoice_policy(self, sale):
        return True

    def set_cheapest_delivery_carrier(self, sale, data):
        return sale.assign_cheapest_delivery_carrier()

    def set_sale_agent(self, sale, data):
        return

    def create_extra_sale_attachments(self, sale, data):
        attachment_obj = self.env['ir.attachment']
        for attachment in data['attachments']:
            try:
                attachment_obj.create({
                    'name': attachment['name'].split('.')[0],
                    'type': attachment['type'],
                    'mimetype': attachment['mimetype'],
                    'datas_fname': attachment['name'],
                    'datas': attachment['datas'],
                    'res_model': 'sale.order',
                    'res_id': sale.id,
                })
            except Exception as e:
                raise ValidationError(
                    _('Error attaching files %s' % str(e)))

    def check_line_price_error(self, line, line_total_taxed, index):
        if line.discount != 100 and abs(line_total_taxed - (
                line.price_tax + line.price_subtotal)) > 0.6:
            msg = (
                _('Line/Product [%s/%s]: Price with taxes does not match '
                  'with calculated by Odoo:\nLine taxes in JSON: %s\n'
                  'Total line taxes calculated by Odoo: %s') % (
                    index, line.product_id.default_code,
                    line_total_taxed,
                    line.price_tax + line.price_subtotal))
            if self.env.user.company_id.action_msg_price == 'raise_error':
                raise ValidationError(msg)
            elif self.env.user.company_id.action_msg_price == 'post_note':
                line.order_id.message_post(body=msg)

    @api.model
    def json_import(self, json_content):
        json_content = copy.deepcopy(json_content)

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
            if 'id' in data and isinstance(data['id'], int):
                partner = self.env['res.partner'].browse(data['id']).exists()
                if not partner:
                    raise ValidationError(
                        _('Partner id is not valid. Please review it.'))
                return partner
            partners = self.env['res.partner']
            if data.get('email', False):
                partners = self.env['res.partner'].search([
                    ('email', '=', data['email']),
                ])
            else:
                domain = []
                for key, value in data.items():
                    if value:
                        domain.append((key, '=', data[key]))
                partners = self.env['res.partner'].search(domain)
            if not partners:
                partners = self.env['res.partner'].create(data)
            if len(partners) > 1:
                raise ValidationError(
                    _('Multiple partners with same email "%s"' % (
                        json_content['partner']['email'])))
            return partners

        def partner_shipping_get_or_create(data):
            if 'id' in data:
                partner = self.env['res.partner']
                if isinstance(data['id'], int):
                    partner = self.env['res.partner'].browse(
                        data['id']).exists()
                elif isinstance(data['id'], str) and data['id']:
                    partner = self.env['res.partner'].browse(
                        int(data['id'])).exists()
                if not partner and data['id']:
                    raise ValidationError(_('Partner shipping id is not '
                                            'valid. Please review it.'))
                if partner:
                    return partner
            domain = []
            for key, value in data.items():
                if value:
                    domain.append((key, '=', data[key]))
            partners = self.env['res.partner'].search(domain)
            if 'email' in data:
                parent = self.env['res.partner'].search([
                    ('email', '=', data['email']),
                ])
                if parent:
                    data.update({
                        'parent_id': parent.id,
                        'email': False,
                        'type': 'delivery',
                    })
            if 'name' not in data and 'street' in data:
                data['name'] = data['street']
            if not partners:
                partners = self.env['res.partner'].create(data)
            if len(partners) > 1:
                raise ValidationError(
                    _('Multiple partners shipping "%s" with same info' % (
                        json_content['partner']['email'])))
            return partners

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
        data['name'] = '/'
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
        sale.import_by_json = True
        self.get_partner_invoice_policy(sale, json_content)
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
        supplierinfo_list = []
        for index, line in enumerate(json_content['order_line'], start=1):
            supplierinfo = False
            if line.get('product_id', False):
                products = self.env['product.product'].browse(
                    int(line['product_id']))
            else:
                products = self.env['product.product'].search([
                    '|',
                    ('default_code', '=', line['default_code']),
                    ('barcode', '=', line['default_code']),
                ])
            if not products:
                supplierinfo = self.env['product.supplierinfo'].search([
                    ('product_code', '=', line['default_code']),
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
            supplierinfo_data = {
                'supplierinfo_id': (
                    line['supplierinfo_id']
                    if 'supplierinfo_id' in line
                    else False
                ),
            }
            data = clean_content(sale_line_obj, line)
            data.update({
                'order_id': sale.id,
                'product_id': products.id,
                'price_unit': line['price_unit_untaxed'],
            })
            if not line['price_unit_untaxed']:
                tax_percent = 0
            else:
                tax_percent = round(
                    float(line['price_unit_taxed']) / float(
                        line['price_unit_untaxed']), 2)
            line_total_taxed = (
                float(line['price_unit_untaxed']) * float(
                    line['product_uom_qty']) * tax_percent)
            discount = line.get('discount', 0)
            if discount > 0 and discount < 100:
                line_total_taxed = line_total_taxed * (
                    1 - line['discount'] / 100)
            line = self.create_with_onchange(sale_line_obj, data)
            supplierinfo_data['line_id'] = line.id
            supplierinfo_list.append(supplierinfo_data)
            if discount and line.discount != discount:
                line.discount = discount
            self.check_line_price_error(line, line_total_taxed, index)
            if supplierinfo and 'supplierinfo_id' in sale_line_obj._fields:
                line.write({
                    'supplierinfo_id': supplierinfo.id,
                    'vendor_id': supplierinfo.name.id,
                })
        if not json_content.get('carrier_id', False):
            self.set_cheapest_delivery_carrier(sale, json_content)
        if sale.carrier_id:
            sale.get_delivery_price()
        if 'agent_id' in json_content or 'agent_name' in json_content:
            self.set_sale_agent(sale, json_content)
        self.env['ir.attachment'].create({
            'name': 'JSON_%s' % sale.name,
            'datas': base64.b64encode(file_json_content.encode()),
            'datas_fname': 'json_%s.json' % sale.name,
            'res_model': 'sale.order',
            'res_id': sale.id,
            'mimetype': 'application/json',
        })
        if json_content.get('attachments'):
            self.create_extra_sale_attachments(sale, json_content)
        self.check_pending_approve(sale, json_content)
        if json_content.get('name'):
            sale.name = json_content['name']
        elif sale.name == '/':
            sale.write({
                'name': (self.env['ir.sequence'].next_by_code('sale.order')
                         or '/')})
        if sale.state == 'pending-approve':
            return sale.id
        if json_content['state'] in [
                'confirmed', 'confirmed-no-payment', 'confirmed-no-invoice']:
            sale.with_context(
                supplierinfo=supplierinfo_list,
                import_by_json=True
            ).sudo(user=self.env.context.get('login_user')).action_confirm()
            if sale.state != 'sale':
                raise ValidationError(_(
                    'The sale order could not be confirmed. The order '
                    'is in status: %s') % sale.state)
            if json_content.get('invoice_date', False):
                sale.confirmation_date = json_content['invoice_date']
            for picking in sale.picking_ids:
                picking.action_confirm()
                picking.action_assign()
            if json_content['state'] == 'confirmed-no-invoice':
                return sale.id
            res = self.check_sale_invoice_policy(sale)
            if res is False:
                return sale.id
            if any(line.qty_to_invoice == 0 for line in sale.order_line):
                raise ValidationError(
                    _('Lines without quantity to be invoiced for order %s' % (
                        json_content['name'])))
            self.create_invoice_from_order(sale, json_content)
        return sale.id

    def create_invoice_from_order(self, sale, json_content):

        def savepoint(name):
            self._cr.execute('SAVEPOINT %s' % name)

        def rollback(name):
            self._cr.execute('ROLLBACK TO SAVEPOINT %s' % name)
            self.pool.clear_caches()
            self.pool.reset_changes()

        def release(name):
            self._cr.execute('RELEASE SAVEPOINT %s' % name)

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

        if sale.state != 'sale':
            raise ValidationError(_(
                'The sale order should be confirmed. The order is in status: '
                '%s') % sale.state)
        savepoint('sale_order_import_json')
        try:
            sale.action_invoice_create()
            if json_content.get('invoice_number', False) and (
                    len(sale.invoice_ids) > 1):
                rollback('sale_order_import_json')
                raise ValidationError(_(
                    'The sales order has generated several invoices.'))
            release('sale_order_import_json')
        except Exception as e:
            raise e
        for invoice in sale.invoice_ids:
            if json_content.get('invoice_date', False):
                invoice.date_invoice = json_content['invoice_date']
            invoice.action_invoice_open()
            if invoice.state == 'paid':
                return True
            if json_content.get('invoice_number', False):
                invoice.number = json_content['invoice_number']
                invoice.invoice_number = json_content['invoice_number']
            if json_content['state'] == 'confirmed':
                journal = sale.team_id and (
                    sale.team_id.import_payment_journal_id or False)
                if json_content.get('payment_journal_name', False):
                    journal = get_journal(
                        json_content['payment_journal_name'])
                if not journal:
                    raise ValidationError(_(
                        'For payment procces you must pass a '
                        'payment_journal_name params or configure sales '
                        'team.'))
                if journal.type not in ['bank', 'cash']:
                    raise ValidationError(
                        _('The journal "%s" must be the type bank or '
                          'cash.') % journal.name)
                payment_method = journal.inbound_payment_method_ids or False
                if json_content.get('payment_method_name', False):
                    payment_method = get_payment_method(
                        json_content['payment_method_name'])
                if not payment_method:
                    raise ValidationError(_(
                        'For payment procces you must pass a '
                        'payment_method_name params or configure journal.'))
                payment = self.env['account.payment'].with_context(
                    active_model='account.invoice',
                    active_id=invoice.id,
                    active_ids=invoice.ids
                ).create({
                    'name': sale.name,
                    'payment_method_id': payment_method[0].id,
                    'journal_id': journal.id,
                })
                if payment and json_content.get('invoice_date', False):
                    payment.payment_date = json_content['invoice_date']
                payment.action_validate_invoice_payment()
        return True

    @api.model
    def json_import_create_invoice(self, json_content):
        json_content = copy.deepcopy(json_content)

        def get_sale_order(data):
            orders = self.env['sale.order'].search([
                ('name', '=', data),
            ])
            if not orders:
                raise ValidationError(
                    _('Sale order with name "%s" not found.' % (data)))
            if len(orders) > 1:
                raise ValidationError(
                    _('Multiple sale orders with same name "%s".' % (data)))
            if orders.invoice_ids:
                raise ValidationError(
                    _('The sale order "%s" already has invoices.' % (data)))
            return orders

        sale = get_sale_order(json_content.get('name', False))
        if json_content.get('invoice_number', False):
            invoices = self.env['account.invoice'].search([
                ('number', '=', json_content['invoice_number']),
            ])
            if invoices:
                raise ValidationError(_(
                    'Already exists an invoice with number '
                    '"%s".' % json_content['invoice_number']))
        if not json_content.get('state', False):
            json_content['state'] = 'confirmed'
        self.create_invoice_from_order(sale, json_content)
        file_json_content = json.dumps(json_content, indent=4, sort_keys=True)
        for invoice in sale.invoice_ids:
            self.env['ir.attachment'].create({
                'name': 'JSON_%s' % sale.name,
                'datas': base64.b64encode(file_json_content.encode()),
                'datas_fname': 'json_%s.json' % sale.name,
                'res_model': 'account.invoice',
                'res_id': invoice.id,
                'mimetype': 'application/json',
            })
        return sale.invoice_ids.ids
