# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import _, api, fields, models
import re


class ImportTemplateSaleAmazon(models.TransientModel):
    _name = 'import.template.sale_amazon'
    _description = 'Template for import sale Amazon file'

    @api.model
    def _default_pricelist_id(self):
        return self.env['product.pricelist'].search([
            ('type', '=', 'sale'),
        ], limit=1)

    @api.model
    def _default_carrier_id(self):
        return self.env['delivery.carrier'].search([], limit=1)

    @api.model
    def _default_payment_mode_id(self):
        return self.env['payment.mode'].search([], limit=1)

    @api.model
    def _default_shipping_product_id(self):
        return self.env['product.product'].search([
            ('type', '=', 'service'),
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
    shipping_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Shipping product',
        default=_default_shipping_product_id,
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

    @api.multi
    def partner_id_get_or_create(self, name):
        errors = []
        if not name:
            errors.append(_('Partner name %s not found.') % name)
            return None, errors
        partners = self.env['res.partner'].search([('name', '=', name)])
        if len(partners) > 1:
            errors.append(_('More than one partner found for %s.') % name)
        if not partners:
            partners = self.env['res.partner'].create({'name': name})
        return partners[0].id, errors

    @api.multi
    def premap_fields(self, df):
        map_data = {
            'order-id': 'origin',
            'ship-address-1': 'street',
            'ship-address-2': 'street2',
            'ship-city': 'city',
            'ship-postal-code': 'zip',
            'ship-state': 'state_id',
            'ship-country': 'country_id',
            'sku': 'default_code',
            'quantity-purchased': 'product_uom_qty',
            'vat-exclusive-item-price': 'price_unit',
            'vat-exclusive-shipping-price': 'vat-exclusive-shipping-price',
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
                'Country code \'%s\' not found; \'No country\' is '
                'assigned.') % code)
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
            warns.append(_(
                'State name \'%s\' not found; not assigned.') % state_name)
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
            errors.append(_('Default code %s not found.') % default_code)
            return None, errors
        if isinstance(default_code, float) and default_code % 1 == 0.0:
            default_code = str(int(default_code))
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
    def get_sale_data(self, df, index):
        errors = []
        partner_names = [df['recipient-name'][index], df['buyer-name'][index]]
        partner_name = ' - '.join([p for p in partner_names if p])
        partner_id, errors = self.partner_id_get_or_create(partner_name)
        if df['origin'][index] is None:
            errors.append((_('Column \'order_id\' cannot be empty.')))
            return {}, errors
        data = {
            'origin': 'Amazon sale number: %s' % df['origin'][index],
            'pricelist_id': self.pricelist_id.id,
            'carrier_id': self.carrier_id.id,
            'payment_mode_id': self.payment_mode_id.id,
            'partner_id': partner_id,
        }
        return data, errors

    @api.multi
    def get_line_data(self, df, index, data):
        product_id, errors = self._get_product_id(df['default_code'][index])
        if product_id is None:
            errors.append((_('Column \'product_id\' cannot be empty.')))
            return {}, errors
        product = self.env['product.product'].browse(product_id)
        data.update({
            'name': product.name,
            'product_id': product_id,
            'price_unit': (
                round(df['price_unit'][index] / df['product_uom_qty'][index],
                    2)),
            'product_uom_qty': df['product_uom_qty'][index],
            'vat-exclusive-shipping-price': (
                df['vat-exclusive-shipping-price'][index]),
        })
        return data, errors

    @api.multi
    def get_partner_data(self, df, index):
        partner_warns = []
        country_id, warns = self._get_country_id(df['country_id'][index])
        for warn in warns:
            partner_warns.append(warn)
        state_id, warns = self._get_state_id(
            df['state_id'][index], country_id)
        for warn in warns:
            partner_warns.append(warn)
        try:
            phone = int(df['buyer-phone-number'][index]) or ''
        except Exception:
            phone = (
                df['buyer-phone-number'][index] and int(re.sub(
                    '[^0-9]', '', str(df['buyer-phone-number'][index]))) or '')
        data = {
            'email': df['buyer-email'][index] or '',
            'phone': phone,
            'vat': 'ES01234567L',
            'street': df['street'][index] or '',
            'street2': df['street2'][index] or '',
            'city': df['city'][index] or '',
            'zip': (
                df['zip'][index] and str(int(df['zip'][index])).zfill(5) or
                ''),
            'state_id': state_id,
            'country_id': country_id,
        }
        if not data['email']:
            partner_warns.append(_('Email data not found; not assigned.'))
        if not data['phone']:
            partner_warns.append(_('Phone data not found; not assigned.'))
        if not data['street'] and not data['street2']:
            partner_warns.append(_('Street data not found; not assigned.'))
        if not data['city']:
            partner_warns.append(_('City data not found; not assigned.'))
        if not data['zip']:
            partner_warns.append(_('Zip data not found; not assigned.'))
        return data, partner_warns

    @api.multi
    def get_shipping_line_data(self, shipping_price):
        return {
            'name': self.shipping_product_id.name,
            'product_id': self.shipping_product_id.id,
            'price_unit': shipping_price,
            'product_uom_qty': 1,
        }

    @api.multi
    def update_partner(self, partner_id, df, index, row_index):
        warns = []
        partner = self.env['res.partner'].browse(partner_id)
        data, warns = self.get_partner_data(df, index)
        partner.write(data)
        return warns

    @api.multi
    def check_order(
            self, wizard, amazon_sale_number, data, row_indexs, simulation):
        errors = []
        orders_with_origin = self.env['sale.order'].search([
            ('origin', '!=', False),
        ])
        orders = self.env['sale.order']
        for order in orders_with_origin:
            if amazon_sale_number in order.origin:
                orders |= order
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
            else:
                msg = _(
                    'The order with origin \'%s\' cannot be modified '
                    'because it is not in a draft state.') % (
                    orders.origin)
                errors.append((row_indexs, [msg]))
        else:
            if simulation is False:
                self.env['sale.order'].create(data)
        return errors

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
                'order-id', 'recipient-name', 'buyer-name', 'sku',
                'vat-exclusive-item-price', 'vat-exclusive-shipping-price'
            ])
        self.premap_fields(df)
        wizard.total_rows = len(df)
        all_errors = []
        all_warns = []
        orm_errors = False
        data_orders = {}
        for index, row in df.iterrows():
            wizard.savepoint('import_template_sale_amazon')
            row_index = index + 2
            wizard.step(index + 1, 'Import "%s".' % row['origin'])
            data, errors = wizard.get_data_row(
                self, 'sale.order.line', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('sale.order.line', data)
            for error in errors:
                all_errors.append((row_index, [error]))
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
                wizard.rollback('import_template_sale_amazon')
                continue
            row_error = any([
                e for e in all_errors
                if e[0] == row_index and e[1] != [] and e[1] != [[]]])
            if row_error:
                wizard.rollback('import_template_sale_amazon')
                continue
            if data_order.get('origin', None):
                amazon_sale_number = (
                    data_order['origin'].split(': ') and
                    data_order['origin'].split(': ')[1] or '')
                if amazon_sale_number not in data_orders:
                    data_orders[amazon_sale_number] = {
                        'order_line': []
                    }
                if not data_line:
                    del data_orders[amazon_sale_number]
                else:
                    data_orders[amazon_sale_number].update(data_order)
                    shipping_price = data_line['vat-exclusive-shipping-price']
                    data_line.pop('vat-exclusive-shipping-price')
                    data_orders[amazon_sale_number]['order_line'].extend([
                        (0, 0, data_line)])
                    if shipping_price:
                        data_shipp_line = self.get_shipping_line_data(
                            shipping_price)
                        data_orders[amazon_sale_number][
                            'order_line'].extend([(0, 0, data_shipp_line)])
        for amazon_sale_number, data_order in data_orders.items():
            wizard.savepoint('import_template_sale_amazon')
            row_indexs = self.get_row_index_by_column(
                df, 'origin', amazon_sale_number)
            try:
                errors = self.check_order(
                    wizard, amazon_sale_number, data_order, row_indexs,
                    simulation)
                for error in errors:
                    all_errors.append(error)
                wizard.release('import_template_sale_amazon')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_indexs, [e]))
                wizard.rollback('import_template_sale_amazon')
        _add_warns(all_warns)
        _add_errors(all_errors)
        return not orm_errors
