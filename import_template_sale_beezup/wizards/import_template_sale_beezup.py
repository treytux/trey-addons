# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import _, api, fields, models, tools
from openerp.tools.float_utils import float_round
import re


class ImportTemplateSaleBeezup(models.TransientModel):
    _name = 'import.template.sale_beezup'
    _description = 'Template for import sale Beezup file'

    @api.model
    def _default_pricelist_id(self):
        return self.env['product.pricelist'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'sale'),
        ], limit=1)

    @api.model
    def _default_carrier_id(self):
        return self.env['delivery.carrier'].search([], limit=1)

    @api.model
    def _default_payment_mode_id(self):
        return self.env['payment.mode'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)

    @api.model
    def _default_journal_sale_id(self):
        return self.env['account.journal'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'sale'),
        ], limit=1)

    @api.model
    def _default_journal_payment_id(self):
        return self.env['account.journal'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('type', 'in', ['bank', 'cash']),
        ], limit=1)

    @api.model
    def _default_partner_account_id(self):
        return self.env['account.account'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'receivable'),
        ], limit=1)

    @api.model
    def _default_shipping_product_id(self):
        return self.env['product.product'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'service'),
        ], limit=1)

    @api.model
    def _default_fiscal_position_id(self):
        return self.env['account.fiscal.position'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('country_id', '=', self.env.ref('base.es').id),
        ], limit=1)

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        default=_default_pricelist_id,
    )
    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
        default=_default_carrier_id,
    )
    payment_mode_id = fields.Many2one(
        comodel_name='payment.mode',
        string='Payment mode',
        default=_default_payment_mode_id,
    )
    journal_sale_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal sale',
        default=_default_journal_sale_id,
        help='Sales journal to be assigned to the invoice, if created.'
    )
    partner_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Partner account',
        default=_default_partner_account_id,
        domain="[('type', '=', 'receivable')]",
        help='Partner\'s account receivable to be assigned to the invoice '
             'lines, if created.'
    )
    shipping_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Shipping product',
        default=_default_shipping_product_id,
    )
    journal_payment_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal payment',
        default=_default_journal_payment_id,
        domain=[('type', 'in', ['bank', 'cash'])],
        help='Payment journal to pay the invoice, if created.'
    )
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Spanish fiscal position',
        default=_default_fiscal_position_id,
        help='Tax position for calculating prices and taxes for country code '
             '\'ES\'.'
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('select_template', 'Template selection'),
            ('data', 'Data required'),
            ('simulation', 'Simulation'),
            ('step_done', 'Done'),
            ('orm_error', 'Errors'),
        ],
        required=True,
        readonly=True,
        default='data',
    )
    force_partner = fields.Boolean(
        string='Force partner',
        help='If you check this field, you must fill the "Parent company" '
             'field and each contact that is imported will be assigned that '
             'company as the parent. Also, in the generated sales order, this '
             'parent company will be assigned as the invoice address.',
    )
    parent_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Parent partner',
    )

    @api.multi
    def _parse_with_cast(self, cast, value):
        try:
            return cast(str(value).strip())
        except Exception:
            return None

    @api.multi
    def _parse_float(self, value):
        value = ''.join([
            v for v in str(value).replace(',', '.') if v in '0123456789+-.'])
        return 0.0 if value == '' else self._parse_with_cast(float, value)

    @api.multi
    def partner_id_get_or_create(self, name):
        errors = []
        if not name:
            errors.append(_('Partner empty not found.'))
            return None, errors
        partners = self.env['res.partner'].search([('name', '=', name)])
        if len(partners) > 1:
            errors.append(_('More than one partner found for %s.') % name)
        if not partners:
            partners = self.env['res.partner'].create({
                'name': name,
                'property_account_receivable': self.partner_account_id.id,
            })
        if self.force_partner:
            partners[0].parent_id = self.parent_partner_id.id
        return partners[0].id, errors

    @api.multi
    def premap_fields(self, df):
        map_data = {
            'Order_MarketPlaceOrderId': 'origin',
            'Order_Buyer_Email': 'email',
            'Order_Shipping_Phone': 'phone',
            'Order_Shipping_MobilePhone': 'mobile',
            'Order_Shipping_AddressLine1': 'street',
            'Order_Shipping_AddressLine2': 'street2',
            'Order_Shipping_AddressCity': 'city',
            'Order_Shipping_AddressPostalCode': 'zip',
            'Order_Shipping_AddressStateOrRegion': 'state_id',
            'Order_Shipping_AddressCountryIsoCodeAlpha2': 'country_id',
            'OrderItem_MerchantImportedProductId': 'default_code',
            'OrderItem_Quantity': 'product_uom_qty',
            'OrderItem_ItemPrice': 'price_unit',
            'OrderItem_Shipping_Price': 'OrderItem_Shipping_Price',
            'Order_TotalPrice': 'Order_TotalPrice',
            'Order_MarketPlaceChannel': 'Order_MarketPlaceChannel',
            'Order_Status_MarketPlaceStatus': 'Order_Status_MarketPlaceStatus',
        }
        cols_parsed = list(df.columns.copy())
        for index, c in enumerate(df.columns):
            if c in map_data.keys():
                cols_parsed.remove(c)
                cols_parsed.insert(index, map_data[c])
        df.columns = cols_parsed
        return df

    @api.multi
    def _get_country_id(self, code):
        warns = []
        no_country = self.env.ref('import_template.no_country')
        assert no_country, 'no_country no exist.'
        if not code:
            warns.append(_(
                'Country code empty not found; \'No country\' is assigned.'))
            return no_country.id, warns
        countries = self.env['res.country'].with_context(
            lang='es_ES').search([('code', '=', code)])
        if len(countries) > 1:
            countries = countries[0]
            warns.append(_(
                'More than one country found for \'%s\', the first is '
                'assigned.') % code)
        if not countries:
            warns.append(_(
                'The country \'%s\' does not exist; \'No country\' is '
                'assigned.') % code)
            return no_country.id, warns
        return countries[0].id, warns

    @api.multi
    def _get_state_id(self, state_name, country_id):
        warns = []
        if not state_name:
            warns.append(_('State name empty not found; not assigned.'))
            return None, warns
        domain = [
            ('name', 'ilike', state_name.strip()),
        ]
        if country_id:
            domain.append(('country_id', '=', country_id))
        states = self.env['res.country.state'].with_context(
            lang='es_ES').search(domain)
        if len(states) > 1:
            states = states[0]
            warns.append(_(
                'More than one state found for \'%s\', the first is '
                'assigned.') % state_name)
        if not states:
            if country_id:
                data = {
                    'name': state_name.strip().capitalize(),
                    'code': '00',
                    'country_id': country_id,
                }
            else:
                no_country = self.env.ref('import_template.no_country')
                assert no_country, 'no_country no exist.'
                data.update({
                    'country_id': no_country.id,
                })
            state = self.env['res.country.state'].create(data)
            return state.id, warns
        return states[0].id, warns

    @api.multi
    def _get_product_id(self, default_code):
        errors = []
        if not default_code:
            errors.append(_('Default code empty not found.'))
            return None, errors
        if isinstance(default_code, float) and default_code % 1 == 0.0:
            default_code = str(int(default_code))
        if isinstance(default_code, (str, unicode)):
            default_code = default_code.replace(
                '-FBAAA', '').replace('-FBAA', '').replace('-FBA', '')
        products = self.env['product.product'].search([
            ('default_code', '=', default_code)])
        if len(products) > 1:
            errors.append(_(
                'More than one product found for %s.') % default_code)
        if not products:
            errors.append(_(
                'The product \'%s\' does not exist.') % default_code)
            return None, errors
        return products[0].id, errors

    @api.multi
    def search_fiscal_position(self, country):
        errors = []
        warns = []
        fiscal_positions = self.env['account.fiscal.position'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('country_id', '=', country.id),
        ])
        if not fiscal_positions:
            errors.append(_(
                'No fiscal position found for country code \'%s\'.') % (
                country.code))
            return {}, warns, errors
        elif len(fiscal_positions) > 1:
            errors.append(_(
                'More than one fiscal position found for country code '
                '\'%s\'.') % country.code)
            return {}, warns, errors
        return fiscal_positions, warns, errors

    @api.multi
    def get_fiscal_position(self, df, index):
        errors = []
        warns = []
        if not df['country_id'][index]:
            warns.append(_(
                'Country code empty not found; \'No country\' will be '
                'assigned.'))
            no_country = self.env.ref('import_template.no_country')
            assert no_country, 'no_country no exist.'
            fiscal_positions, warns_fp, errors_fp = (
                self.search_fiscal_position(no_country))
            for warn in warns_fp:
                warns.append(warn)
            for error in errors_fp:
                errors.append(error)
            return fiscal_positions, warns, errors
        if df['country_id'][index] == 'ES':
            fiscal_positions = self.fiscal_position_id
        else:
            country_id, warns_country = self._get_country_id(
                df['country_id'][index])
            for warn in warns_country:
                warns.append(warn)
            country = self.env['res.country'].browse(country_id)
            fiscal_positions, warns_fp, errors_fp = (
                self.search_fiscal_position(country))
            for warn in warns_fp:
                warns.append(warn)
            for error in errors_fp:
                errors.append(error)
            return fiscal_positions, warns, errors
        return fiscal_positions, warns, errors

    @api.multi
    def get_sale_data(self, df, index):
        errors = []
        partner_id, errors = self.partner_id_get_or_create(
            df['Order_Shipping_AddressName'][index])
        if df['origin'][index] is None:
            errors.append((_('Column \'order_id\' cannot be empty.')))
            return {}, errors
        data = {
            'origin': 'Beezup sale number: %s' % df['origin'][index],
            'pricelist_id': self.pricelist_id.id,
            'carrier_id': self.carrier_id.id,
            'payment_mode_id': self.payment_mode_id.id,
            'partner_id': partner_id,
            'partner_shipping_id': partner_id,
            'partner_invoice_id': (
                self.force_partner and self.parent_partner_id.id or
                partner_id),
            'Order_TotalPrice': self._parse_float(
                df['Order_TotalPrice'][index]),
            'Order_MarketPlaceChannel': df['Order_MarketPlaceChannel'][index],
        }
        return data, errors

    @api.multi
    def get_line_data(self, df, index, data):
        product_id, errors = self._get_product_id(df['default_code'][index])
        if product_id is None:
            errors.append((_('Column \'product_id\' cannot be empty.')))
            return {}, errors
        product = self.env['product.product'].browse(product_id)
        precision = self.env['decimal.precision'].precision_get(
            'Product Price')
        taxs = self.fiscal_position.map_tax(product.taxes_id)
        amount_taxs = sum(tax.amount for tax in taxs)
        price_without_taxs = float_round(
            data['price_unit'] / (1 + amount_taxs), precision)
        data.update({
            'name': product.name,
            'product_id': product_id,
            'product_uom_qty': data['product_uom_qty'],
            'price_unit': price_without_taxs,
            'tax_id': [(6, 0, [t.id for t in taxs])],
            'OrderItem_Shipping_Price': (
                self._parse_float(df['OrderItem_Shipping_Price'][index])),
        })
        return data, errors

    @api.multi
    def get_partner_data(self, df, index):
        partner_warns = []
        country_id, warns = self._get_country_id(df['country_id'][index])
        for warn in warns:
            partner_warns.append(warn)
        state_id, warns = self._get_state_id(df['state_id'][index], country_id)
        for warn in warns:
            partner_warns.append(warn)
        other_streets = [
            df['street2'][index], df['Order_Shipping_AddressLine3'][index]]
        other_street = ' - '.join([p for p in other_streets if p])
        try:
            phone = df['phone'][index] and int(df['phone'][index]) or ''
            mobile = df['mobile'][index] and int(df['mobile'][index]) or ''
        except Exception:
            phone = df['phone'][index] or ''
            mobile = df['mobile'][index] or ''
        data = {
            'email': df['email'][index] or '',
            'phone': phone,
            'mobile': mobile,
            'vat': (
                self.force_partner and self.parent_partner_id.vat or
                'ES01234567L'),
            'street': df['street'][index] or '',
            'street2': other_street,
            'city': df['city'][index] or '',
            'zip': df['zip'][index] and int(df['zip'][index]) or '',
            'state_id': state_id,
            'country_id': country_id,
            'property_account_position': (
                self.force_partner and
                self.parent_partner_id.property_account_position and
                self.parent_partner_id.property_account_position.id or
                self.fiscal_position.id),
        }
        if not data['email']:
            partner_warns.append(_('Email data not found; not assigned.'))
        if not data['phone'] and not data['mobile']:
            partner_warns.append(_(
                'Phone and mobile data not found; not assigned.'))
        if not data['street'] and not data['street2']:
            partner_warns.append(_('Street data not found; not assigned.'))
        if not data['city']:
            partner_warns.append(_('City data not found; not assigned.'))
        if not data['zip']:
            partner_warns.append(_('Zip data not found; not assigned.'))
        return data, partner_warns

    @api.multi
    def get_shipping_line_data(self, shipping_price):
        precision = self.env['decimal.precision'].precision_get(
            'Product Price')
        taxs = self.fiscal_position.map_tax(self.shipping_product_id.taxes_id)
        amount_taxs = sum(tax.amount for tax in taxs)
        price_without_taxs = float_round(
            shipping_price / (1 + amount_taxs), precision)
        return {
            'name': self.shipping_product_id.name,
            'product_id': self.shipping_product_id.id,
            'price_unit': price_without_taxs,
            'product_uom_qty': 1,
            'tax_id': [(6, 0, [t.id for t in taxs])],
        }

    @api.multi
    def update_partner(self, partner_id, df, index, row_index):
        warns = []
        partner = self.env['res.partner'].browse(partner_id)
        data, warns = self.get_partner_data(df, index)
        if not partner.property_account_receivable:
            data.update({
                'property_account_receivable': self.partner_account_id.id,
            })
        partner.write(data)
        return warns

    def pay_invoice(self, invoice):
        res = invoice.invoice_pay_customer()
        voucher_context = res['context']
        update = {}
        for dkey in voucher_context:
            if not dkey.startswith('default_'):
                continue
            key = re.sub(r'^default_', '', dkey)
            if voucher_context.get(key):
                continue
            update[key] = voucher_context[dkey]
        voucher_context.update(update)
        field_list = [
            'comment',
            'line_cr_ids',
            'is_multi_currency',
            'paid_amount_in_company_currency',
            'line_dr_ids',
            'journal_id',
            'currency_id',
            'narration',
            'partner_id',
            'payment_rate_currency_id',
            'reference',
            'writeoff_acc_id',
            'state',
            'pre_line',
            'type',
            'payment_option',
            'account_id',
            'company_id',
            'period_id',
            'date',
            'payment_rate',
            'name',
            'writeoff_amount',
            'analytic_id',
            'amount',
        ]
        voucher_obj = self.env['account.voucher']
        voucher_values = voucher_obj.with_context(
            voucher_context).default_get(field_list)
        res = voucher_obj.with_context(voucher_context).onchange_journal(
            self.journal_payment_id.id,
            [],  # lines
            [],  # taxes
            voucher_values.get('partner_id'),
            voucher_values.get('date'),
            voucher_values.get('amount'),
            voucher_values.get('ttype'),
            voucher_values.get('company_id'))
        voucher_values.update(res['value'])
        voucher_values.update({'journal_id': self.journal_payment_id.id})
        for key in ['line_dr_ids', 'line_cr_ids']:
            array = []
            for obj in voucher_values[key]:
                array.append([0, False, obj])
            voucher_values[key] = array
        voucher = voucher_obj.with_context(voucher_context).create(
            voucher_values)
        voucher.with_context(voucher_context).button_proforma_voucher()

    @api.multi
    def process_order(self, order, row_indexs):
        warns = []
        # Crear factura: Sobre la orden de entrega
        # Para simular el valor po defecto en los test
        if tools.config['test_enable']:
            order.order_policy = 'picking'

        if order.order_policy != 'picking':
            msg = _(
                'The order policy of the order with origin %s is %s and is '
                'not contemplated, so the invoice has not been created; check '
                'manually.' % (order.origin, order.order_policy))
            warns.append((row_indexs, [msg]))
            return warns
        order.signal_workflow('order_confirm')
        if not order.picking_ids:
            msg = _(
                'The order with origin \'%s\' has not generated picking, '
                'check manually.' % order.origin)
            warns.append((row_indexs, [msg]))
            return warns
        if len(order.picking_ids) > 1:
            msg = _(
                'The order with origin \'%s\' has more than one picking '
                'associated, check manually.' % order.origin)
            warns.append((row_indexs, [msg]))
            return warns
        picking_out = order.picking_ids[0]
        if picking_out.picking_type_code != 'outgoing':
            msg = _(
                'The picking associated with the order with origin \'%s\' is '
                'not of type output associated, check manually.' % (
                    order.origin))
            warns.append((row_indexs, [msg]))
            return warns
        picking_out.action_confirm()
        picking_out.force_assign()
        picking_out.do_transfer()
        if picking_out.state != 'done':
            msg = _(
                'The picking out associated with the order with origin \'%s\' '
                'has not been transferred correctly, check manually.' % (
                    order.origin))
            warns.append((row_indexs, [msg]))
            return warns
        invoice_ids = picking_out.with_context(
            inv_type='out_invoice').action_invoice_create(
                self.journal_sale_id.id, type='out_invoice')
        if not invoice_ids:
            msg = _(
                'The stock picking %s of the order with origin %s has not '
                'generated invoice; check manually.' % (
                    picking_out.name, order.origin))
            warns.append((row_indexs, [msg]))
            return warns
        if len(invoice_ids) > 1:
            msg = _(
                'More than one invoice has been generated from the stock '
                'picking of the order with origin %s; check manually.' % (
                    order.origin))
            warns.append((row_indexs, [msg]))
            return warns
        invoice = self.env['account.invoice'].browse(invoice_ids[0])
        invoice.signal_workflow('invoice_open')
        if invoice.state != 'open':
            msg = _(
                'The invoice associated with the order with origin \'%s\' has '
                'not been opened correctly, check manually.' % order.origin)
            warns.append((row_indexs, [msg]))
            return warns
        self.pay_invoice(invoice)
        if invoice.state != 'paid':
            msg = _(
                'The invoice associated with the order with origin \'%s\' has '
                'not been paid correctly, check manually.' % order.origin)
            warns.append((row_indexs, [msg]))
            return warns
        wizard = self.env['stock.return.picking'].with_context(
            active_id=picking_out.id).create({
                'invoice_state': '2binvoiced',
            })
        picking_return_id, pick_type_id = wizard.with_context(
            active_id=picking_out.id)._create_returns()
        if not picking_return_id:
            msg = _(
                'The picking return associated with the order with origin '
                '\'%s\' has not been created correctly, check manually.' % (
                    order.origin))
            warns.append((row_indexs, [msg]))
            return warns
        picking_return = self.env['stock.picking'].browse(picking_return_id)
        picking_return.invoice_state = 'none'
        picking_return.action_confirm()
        picking_return.force_assign()
        picking_return.do_transfer()
        if picking_return.state != 'done':
            msg = _(
                'The picking return associated with the order with origin '
                '\'%s\' has not been transferred correctly, check '
                'manually.' % order.origin)
            warns.append((row_indexs, [msg]))
            return warns
        return warns

    @api.multi
    def check_order(
            self, wizard, beezup_sale_number, data, row_indexs, simulation):

        def _check_amount_total(order, file_total_price):
            if abs(order.amount_total - file_total_price) > 0.02:
                msg = _(
                    'The amount total in order with origin \'%s\' does not '
                    'match with Odoo calcules:\nTotal amount in file: %s\n'
                    'Total amount in Odoo: %s.') % (
                    order.origin, file_total_price, order.amount_total)
                warns.append((row_indexs, [msg]))

        errors = []
        warns = []
        orders_with_origin = self.env['sale.order'].search([
            ('origin', '!=', False),
        ])
        orders = self.env['sale.order']
        for order in orders_with_origin:
            if beezup_sale_number in order.origin:
                orders |= order
        file_total_price = data['Order_TotalPrice']
        data.pop('Order_TotalPrice')
        market_place = data['Order_MarketPlaceChannel']
        data.pop('Order_MarketPlaceChannel')
        if orders:
            if len(orders) > 1:
                msg = _(
                    'More than one sale order with origin \'%s\' has '
                    'been found. The order details could not be '
                    'imported.') % orders[0].origin
                errors.append((row_indexs, [msg]))
            elif orders.state == 'draft':
                if simulation is False:
                    orders.order_line.unlink()
                    orders.write(data)
                    _check_amount_total(orders, file_total_price)
                    if market_place == 'AFN':
                        process_warns = self.process_order(order, row_indexs)
                        for w in process_warns:
                            warns.append(w)
            else:
                msg = _(
                    'The order with origin \'%s\' cannot be modified '
                    'because it is not in a draft state.') % (
                    orders.origin)
                errors.append((row_indexs, [msg]))
        else:
            if simulation is False:
                order = self.env['sale.order'].create(data)
                _check_amount_total(order, file_total_price)
                if market_place == 'AFN':
                    process_warns = self.process_order(order, row_indexs)
                    for w in process_warns:
                        warns.append(w)
        return errors, warns

    @api.multi
    def action_import_file(self):
        if not self._context.get('wizard_id'):
            assert self._context.get('wizard_id'), (
                '\'wizard_id\' must be specified in context.')
        wizard_file = self.env['import.file'].browse(
            self._context['wizard_id'])
        self.import_file(wizard_file.simulate)
        return wizard_file.template_id.open_form(wizard_file)

    @api.multi
    def get_row_index_by_column(self, df, col_name, value):
        indexs = []
        for index, row in df.iterrows():
            if row[col_name] == value:
                indexs.append(index + 2)
        return ', '.join((map(str, indexs)))

    @api.multi
    def import_file(self, simulation=True):
        def _add_warns(warns):
            for warn in warns:
                if warn != [] and warn[1] != [] and warn[1] != [[]]:
                    wizard.warn(warn[0], warn[1][0])

        def _add_errors(errors):
            for error in errors:
                if error != [] and error[1] != [] and error[1] != [[]]:
                    wizard.error(error[0], error[1][0])
        if not self._context.get('wizard_id'):
            assert self._context.get('wizard_id'), (
                '\'wizard_id\' must be specified in context.')
        wizard = self.env['import.file'].browse(self._context['wizard_id'])
        wizard.line_ids.unlink()
        df = wizard.dataframe_get()
        wizard.dataframe_required_columns(
            df, [
                'Order_MarketPlaceOrderId', 'Order_Shipping_AddressName',
                'OrderItem_MerchantImportedProductId', 'OrderItem_ItemPrice',
                'OrderItem_Shipping_Price',
                'Order_Shipping_AddressCountryIsoCodeAlpha2',
            ])
        self.premap_fields(df)
        wizard.total_rows = len(df)
        all_errors = []
        all_warns = []
        orm_errors = False
        data_orders = {}
        for index, row in df.iterrows():
            wizard.savepoint('import_template_sale_beezup')
            row_index = index + 2
            wizard.step(index + 1, 'Import "%s".' % row['origin'])
            data, errors = wizard.get_data_row(
                self, 'sale.order.line', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('sale.order.line', data)
            for error in errors:
                all_errors.append((row_index, [error]))
            if df['Order_Status_MarketPlaceStatus'][index] == 'Canceled':
                msg = _(
                    'Column \'Order_Status_MarketPlaceStatus\' with value '
                    'canceled; the order line will not be imported.')
                all_warns.append((row_index, [msg]))
                continue
            fiscal_positions, warns, errors = self.get_fiscal_position(
                df, index)
            for warn in warns:
                all_warns.append((row_index, [warn]))
            for error in errors:
                all_errors.append((row_index, [error]))
            if not fiscal_positions:
                continue
            self.fiscal_position = fiscal_positions[0]
            data_line, errors = self.get_line_data(df, index, data)
            for error in errors:
                all_errors.append((row_index, [error]))
            data_order, errors = self.get_sale_data(df, index)
            for error in errors:
                all_errors.append((row_index, [error]))
            partner_id = data_order.get('partner_id', None)
            warns = self.update_partner(partner_id, df, index, row_index)
            for warn in warns:
                all_warns.append((row_index, [warn]))
            if simulation:
                wizard.rollback('import_template_sale_beezup')
                continue
            row_error = any([
                e for e in all_errors
                if e[0] == row_index and e[1] != [] and e[1] != [[]]])
            if row_error:
                wizard.rollback('import_template_sale_beezup')
                continue
            if data_order.get('origin', None):
                beezup_sale_number = (
                    data_order['origin'].split(': ') and
                    data_order['origin'].split(': ')[1] or '')
                if beezup_sale_number not in data_orders:
                    data_orders[beezup_sale_number] = {
                        'order_line': [],
                    }
                if not data_line:
                    del data_orders[beezup_sale_number]
                else:
                    data_orders[beezup_sale_number].update(data_order)
                    shipping_price = data_line['OrderItem_Shipping_Price']
                    data_line.pop('OrderItem_Shipping_Price')
                    data_orders[beezup_sale_number]['order_line'].extend([
                        (0, 0, data_line)])
                    if shipping_price:
                        data_shipp_line = self.get_shipping_line_data(
                            shipping_price)
                        data_orders[beezup_sale_number][
                            'order_line'].extend([(0, 0, data_shipp_line)])
        for beezup_sale_number, data_order in data_orders.items():
            wizard.savepoint('import_template_sale_beezup')
            row_indexs = self.get_row_index_by_column(
                df, 'origin', beezup_sale_number)
            try:
                errors, warns = self.check_order(
                    wizard, beezup_sale_number, data_order, row_indexs,
                    simulation)
                for error in errors:
                    all_errors.append(error)
                for warn in warns:
                    all_warns.append(warn)
                wizard.release('import_template_sale_beezup')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_indexs, [e]))
                wizard.rollback('import_template_sale_beezup')
        _add_warns(all_warns)
        _add_errors(all_errors)
        return not orm_errors
