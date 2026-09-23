###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime
import hashlib
import logging
import time
import xml.etree.ElementTree as ET

import requests
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from pytz import timezone

_log = logging.getLogger(__name__)


class VendingMachine(models.Model):
    _name = 'vending.machine'
    _description = 'Vending Machine Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Machine Name',
        readonly=True,
        compute='_compute_name',
    )
    code = fields.Char(
        string='Machine Code',
        help='Code of the vending machine, unique identifier for API requests',
        copy=False,
    )
    signature_key = fields.Char(
        string='Signature Key',
        required=True,
        help='API key for authentication with the vending machine API',
    )
    company_id = fields.Char(
        string='company id',
        required=True,
        help='Reference code for Jofemar vending machines',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Company',
        required=True,
        help='Partner\'s shipping address',
        domain='[("type", "=", "delivery")]',
    )
    parent_id = fields.Many2one(
        comodel_name='res.partner',
        string='Parent Company',
        related='partner_id.parent_id',
        store=True,
        help='Parent company of the vending machine',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        help='Warehouse associated with the vending machine',
    )
    sale_order_count = fields.Integer(
        string='Sale Orders',
        compute='_compute_sale_order_count',
        help='Number of sale orders associated with this vending machine',
    )
    replenish_order_count = fields.Integer(
        string='Replenish Orders',
        compute='_compute_replenish_order_count',
        help='Number of replenish orders associated with this vending machine',
    )
    initial_batch = fields.Integer(
        string='Last Processed Batch',
        copy=False,
        help='Last batch number successfully processed from Jofemar API.',
    )
    temp_initial_batch = fields.Integer(
        string='Temporary Initial Batch',
        copy=False,
        help='Temporary storage for the initial batch number.',
    )
    last_date_stock_deposit = fields.Date(
        string='Last Stock Deposit Date',
        compute='_compute_last_date_stock_deposit',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, it will allow you to hide the product without '
             'removing it.',
    )

    @api.depends('sale_order_count')
    def _compute_last_date_stock_deposit(self):
        for machine in self:
            machine.last_date_stock_deposit = self.env['sale.order'].search([
                ('machine_ids', '=', machine.id),
                ('is_sale_deposit', '=', True),
                ('state', '!=', 'cancel'),
                ('date_stock_deposit', '!=', False),
            ], order='date_stock_deposit desc', limit=1).date_stock_deposit

    @api.constrains('active')
    def _check_active(self):
        machines_with_same_code = self.search([
            ('code', '=', self.code),
        ])
        if len(machines_with_same_code) > 1:
            raise ValidationError(_(
                'There are active vending machines with the same code. '
                'Please ensure that each machine has a unique code.'))

    def _compute_sale_order_count(self):
        for machine in self:
            machine.sale_order_count = self.env['sale.order'].search_count([
                ('machine_ids', '=', machine.id),
                ('is_sale_deposit', '=', True),
            ])

    def _compute_replenish_order_count(self):
        for machine in self:
            machine.replenish_order_count = (
                self.env['sale.order'].search_count([
                    ('machine_ids', '=', machine.id),
                    ('is_sale_deposit', '=', False),
                ]))

    @api.depends('code', 'partner_id')
    def _compute_name(self):
        for machine in self:
            machine.name = f'{machine.code} - {machine.partner_id.parent_name}'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            customer_location = self.partner_id.property_stock_customer
            return {
                'domain': {
                    'location_id': [
                        ('id', '=', customer_location.id),
                    ],
                },
                'value': {
                    'location_id': customer_location.id,
                },
            }

    @api.onchange('location_id')
    def onchange_location_id(self):
        if self.location_id:
            warehouses = self.env['stock.warehouse'].search([
                ('deposit_parent_id', '=', self.location_id.location_id.id),
            ])
            warehouse_id = (
                warehouses and warehouses[0] and warehouses[0].id or None)
            return {
                'domain': {
                    'warehouse_id': [
                        ('id', 'in', warehouses.ids),
                    ],
                },
                'value': {
                    'warehouse_id': warehouse_id,
                },
            }

    def _get_stock_data_from_api(self):
        try:
            get_param = self.env['ir.config_parameter'].sudo().get_param
            param = 'vending_machine.jofemar_api_url'
            api_url = get_param(param, '')
            tz = timezone('Europe/Madrid')
            request_datetime = (datetime.datetime.now().astimezone(
                tz).strftime('%Y-%m-%d %H:%M:%S'))
            signature_str = (f'{self.company_id}{self.code}{request_datetime}'
                             f'{self.signature_key}')
            signature_hash = hashlib.sha1(signature_str.encode()).hexdigest()
            soap_request = f'''<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <GetStockData xmlns="http://compendia.jofemar.com/">
                <CompanyId>{self.company_id}</CompanyId>
                <MachineCode>{self.code}</MachineCode>
                <RequestDateTime>{request_datetime}</RequestDateTime>
                <Signature>{signature_hash}</Signature>
                </GetStockData>
            </soap:Body>
            </soap:Envelope>'''
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': '"http://compendia.jofemar.com/GetStockData"',
            }
            response = requests.post(
                api_url, data=soap_request, headers=headers)
            response.raise_for_status()
            root = ET.fromstring(response.text)
            namespace = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ns': 'http://compendia.jofemar.com/',
            }
            stock_data_list = []
            stock_data_elements = root.findall(
                './/ns:CpxType_StockData', namespace)
            for stock_data in stock_data_elements:
                try:
                    product_code = stock_data.find(
                        'ns:ProductCode', namespace).text
                    current_stock = stock_data.find(
                        'ns:CurrentStock', namespace).text or 0
                    desired_stock = stock_data.find(
                        'ns:DesiredStock', namespace).text or 0
                    selection_number = stock_data.find(
                        'ns:SelectionNumber', namespace).text
                    stock_data_list.append({
                        'selection_number': selection_number,
                        'product_code': product_code,
                        'stock_real': current_stock,
                        'stock_target': desired_stock,
                        'qty_to_replenish': max(0, (
                            int(desired_stock) - int(current_stock))),
                    })
                except (ValueError, AttributeError):
                    continue
            return stock_data_list
        except requests.RequestException:
            return []
        except ET.ParseError:
            return []
        except Exception :
            return []

    def action_view_stock_from_api(self):
        stock_data_list = self._get_stock_data_from_api()
        if not stock_data_list:
            raise UserError(_(
                'Error when synchronizing stock from API. Check the machine '
                'configuration or the API connection.'))
        wizard = self.env['vending.machine.stock'].create({
            'vending_machine_id': self.id,
        })
        if not wizard:
            raise UserError(_(
                'The wizard to update the stock could not be created.'))
        for stock_data in stock_data_list:
            product_code = stock_data.get('product_code')
            if not product_code:
                continue
            product_id = self.env['product.product'].search([
                ('default_code', '=', product_code),
            ], limit=1)
            new_line = self.env['vending.machine.line'].create({
                'wizard_id': wizard.id,
                'product_id': product_id.id if product_id else False,
                'product_code': product_code,
                'selection_number': stock_data.get('selection_number', ''),
                'stock_real': stock_data.get('stock_real', 0),
                'stock_target': stock_data.get('stock_target', 0),
            })
            wizard.product_line_ids += new_line
        module_name = 'vending_machine'
        action_name = 'vending_machine_stock_wizard_action'
        action = self.env.ref(f'{module_name}.{action_name}').read()[0]
        action['res_id'] = wizard.id
        return action

    def initialize_batch_in_one(self):
        self.initial_batch = 1

    def action_request_date_range(self):
        wizard = self.env['vending.machine.move.stock.deposit'].with_context(
            vending_machine_id=self.id).create({
                'vending_machine_id': self.id,
            })
        if not wizard:
            raise UserError(_(
                'The wizard to update the stock could not be created.'))
        module_name = 'vending_machine'
        action_name = 'vending_machine_move_stock_deposit_action'
        action = self.env.ref(f'{module_name}.{action_name}').read()[0]
        action['res_id'] = wizard.id
        return action

    def _get_moves_dispensing_moves(self, from_batch, to_batch):
        try:
            get_param = self.env['ir.config_parameter'].sudo().get_param
            param = 'vending_machine.jofemar_api_url'
            api_url = get_param(param, '')
            tz = timezone('Europe/Madrid')
            request_datetime = (datetime.datetime.now().astimezone(
                tz).strftime('%Y-%m-%d %H:%M:%S'))
            signature_str = (f'{self.company_id}{from_batch}{to_batch}'
                             f'{request_datetime}{self.signature_key}')
            signature_hash = hashlib.sha1(signature_str.encode()).hexdigest()
            soap_request = f'''
                <?xml version="1.0" encoding="utf-8"?>
                <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                            xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                    <soap:Body>
                        <GetExtendedDispensationData
                        xmlns="http://compendia.jofemar.com/">
                        <CompanyId>{self.company_id}</CompanyId>
                        <FromBatch>{from_batch}</FromBatch>
                        <ToBatch>{to_batch}</ToBatch>
                        <RequestDateTime>{request_datetime}</RequestDateTime>
                        <Signature>{signature_hash}</Signature>
                        </GetExtendedDispensationData>
                    </soap:Body>
                </soap:Envelope>
            '''
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': '"http://compendia.jofemar.com/'
                                'GetExtendedDispensationData"',
            }
            response = requests.post(
                api_url, data=soap_request, headers=headers)
            response.raise_for_status()
            root = ET.fromstring(response.text)
            namespace = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ns': 'http://compendia.jofemar.com/',
            }
            error = root.findall('.//ns:ErrorCode', namespace)
            if error:
                error_code = error[0].text
                if error_code != '0':
                    error_message = root.findall(
                        './/ns:ErrorDescription', namespace)[0].text
                    if error_message == 'Wrong batch number(s)':
                        _log.error(f'Error Code: {error_code},'
                                   f' Message: {error_message}')
                        return False
                    else:
                        raise UserError(_(
                            'Error Code: %s, Message: %s'
                        ) % (error_code, error_message))
            move_elements = root.findall(
                './/ns:CpxType_ExtendedDispensationData', namespace)
            moves = []
            for move in move_elements:
                try:
                    product_code = move.find('ns:ProductCode', namespace).text
                    moves.append({
                        'product_id': product_code,
                        'quantity': 1,
                        'machine_code': move.find(
                            'ns:MachineCode', namespace).text,
                        'batch': int(
                            move.find('ns:Batch', namespace).text or 0),
                        'machine_description': move.find(
                            'ns:MachineDescription', namespace).text,
                        'DispenseType': move.find(
                            'ns:DispenseType', namespace).text,
                        'DispenseDateTime': move.find(
                            'ns:DispenseDateTime', namespace).text,
                    })
                except (ValueError, AttributeError):
                    continue
            return moves
        except requests.RequestException as e:
            raise UserError(_('Connection error with Jofemar API: %s') % e)
        except ET.ParseError as e:
            raise UserError(_('XML parsing error from Jofemar API: %s') % e)
        except Exception as e:
            raise UserError(_(
                'An unexpected error occurred when calling ''Jofemar API: %s')
                % e)

    def get_dispensing_moves(self, date_from, date_to, unified_invoice=False,
                             initial_batch=None):
        if not date_from or not date_to:
            raise UserError(_('Please provide a valid date range.'))
        self.ensure_one()
        all_moves = {}
        batch = initial_batch or self.initial_batch
        initial_batch = None
        date_from = datetime.datetime.combine(date_from, datetime.time.min)
        date_to = datetime.datetime.combine(date_to, datetime.time.max)
        machine_ids = []
        missing_product_codes = set()
        code_of_machines_of_partner = self.parent_id.machine_ids.mapped('code')
        if batch == 0:
            self._get_moves_dispensing_moves(batch, batch)
            batch = self.initial_batch + 1
        while True:
            moves = self._get_moves_dispensing_moves(
                batch, batch)
            if isinstance(moves, tuple):
                moves = moves[0] if moves else False
            if moves is False:
                break
            force_break = False
            for move in moves:
                move_date = datetime.datetime.strptime(
                    move.get('DispenseDateTime'), '%Y-%m-%d %H:%M:%S')
                if move_date < date_from:
                    continue
                if move_date > date_to:
                    force_break = True
                    break
                product_id = self.env['product.product'].search([
                    ('default_code', '=', move['product_id']),
                ])
                if not product_id:
                    missing_product_codes.update({move['product_id']})
                    continue
                product_id = product_id.id
                if not unified_invoice and move['machine_code'] != self.code:
                    continue
                if (unified_invoice and move['machine_code']
                        not in code_of_machines_of_partner):
                    continue
                if move['DispenseType'] in ['20', '21', '22', '26', '31']:
                    continue
                move.update({
                    'product_id': product_id,
                })
                all_moves.setdefault(product_id, []).append(move)
                if initial_batch is None:
                    initial_batch = batch
                if int(move['machine_code']) not in machine_ids:
                    machine_ids.append(int(move['machine_code']))
            if force_break:
                break
            batch += 1
        self.temp_initial_batch = initial_batch or batch
        product_sum = {k: len(v) for k, v in all_moves.items()}
        return product_sum, machine_ids, sorted(missing_product_codes)

    def action_move_to_deposit(self, date_from, date_to):
        self._compute_last_date_stock_deposit()
        self.ensure_one()
        if not date_from or not date_to:
            raise UserError(_('Please provide a valid date range.'))
        unified_invoice = (
            self.parent_id.unified_so_for_vending_machines)
        self._get_moves_dispensing_moves(0, 0)
        # The first time, the `initial_batch` parameter is not sent, so it uses
        # `self.initial_batch`, and the second time, the `initial_batch`
        # parameter is sent, so it uses `self.temp_initial_batch` and does not
        # start from 0. `self.initial_batch` is saved when the deposit
        # transaction is confirmed, so that any transactions made between the
        # first and second API calls are not lost.
        moves_machine, machine_codes, missing_product_codes = (
            self.get_dispensing_moves(
                date_from=date_from,
                date_to=date_to,
                unified_invoice=unified_invoice))
        time.sleep(15)
        moves_machine2, machine_codes2, missing_product_codes2 = (
            self.get_dispensing_moves(
                date_from=date_from,
                date_to=date_to,
                unified_invoice=unified_invoice,
                initial_batch=self.temp_initial_batch))
        missing_product_codes = sorted(set(missing_product_codes).union(
            missing_product_codes2))
        for key, value in moves_machine.items():
            try:
                if moves_machine2[key] != value:
                    raise UserError(_(
                        'There are differences between the moves obtained in '
                        'the calls, please try again.'))
            except Exception:
                raise UserError(_(
                    'There are differences between the moves obtained in the'
                    ' calls, please try again.'))
        if not moves_machine and not missing_product_codes:
            raise UserError(_(
                'No there moves for this machine in the last month.'))
        move = self.env['stock.deposit'].create({
            'partner_id': self.partner_id.id,
            'location_id': self.location_id.id,
            'warehouse_id': self.warehouse_id.id,
            'price_option': 'pricelist_partner',
            'create_invoice': False,
            'is_transfer_picking': False,
            'confirm_sale': False,
            'missing_product_codes': '\n'.join(missing_product_codes),
        })
        for key in moves_machine.keys():
            stock_consumed = moves_machine[key]
            product = self.env['product.product'].browse(key).exists()
            if stock_consumed <= 0:
                continue
            if product:
                self.env['stock.deposit.line'].create({
                    'deposit_id': move.id,
                    'product_id': product.id,
                    'qty': stock_consumed,
                })
        action = self.env['ir.actions.actions']._for_xml_id(
            'stock_deposit.stock_deposit_action')
        action['res_id'] = move.id
        action['context'] = {
            'machine_ids': machine_codes,
            'date_from': date_from,
            'last_date_stock_deposit': date_to,
        }
        return action

    def action_view_sale_orders(self):
        self.ensure_one()
        form_view = self.env.ref('sale.view_order_form')
        tree_view = self.env.ref('sale.view_order_tree')
        search_view = self.env.ref('sale.view_sales_order_filter')
        return {
            'name': _('Sale orders'),
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [
                ('machine_ids', '=', self.id),
                ('is_sale_deposit', '=', True),
            ],
        }

    def action_view_replenish_orders(self):
        self.ensure_one()
        form_view = self.env.ref('sale.view_order_form')
        tree_view = self.env.ref('sale.view_order_tree')
        search_view = self.env.ref('sale.view_sales_order_filter')
        return {
            'name': _('Replenish Orders'),
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [
                ('machine_ids', '=', self.id),
                ('is_sale_deposit', '=', False),
            ],
        }

    def replenish_vending_machine(self):
        self.ensure_one()
        stock_data_list = self._get_stock_data_from_api()
        if not stock_data_list:
            raise UserError(_(
                'Error when replenishing the vending machine. Check the machine'
                ' configuration or the API connection.'))
        so = self.env['sale.order']
        with self.env.cr.savepoint():
            sale_order = so.create({
                'partner_id': self.parent_id.id,
                'partner_shipping_id': self.partner_id.id,
                'warehouse_id': self.warehouse_id.id,
                'machine_ids': [(6, 0, [self.id])],
            })
            sale_order.client_order_ref = _(
                'Replenish %s, %s(%s) %s') % (
                self.partner_id.parent_name,
                self.partner_id.name,
                self.code,
                fields.Date.today(),
            )
            for stock_data in stock_data_list:
                qty_to_replenish = stock_data.get('qty_to_replenish', 0)
                product_code = stock_data.get('product_code')
                if qty_to_replenish <= 0 or not product_code:
                    continue
                product_id = self.env['product.product'].search([
                    ('default_code', '=', product_code),
                ], limit=1)
                if not product_id:
                    continue
                self.env['sale.order.line'].create({
                    'order_id': sale_order.id,
                    'product_id': product_id.id,
                    'product_uom_qty': qty_to_replenish,
                })
            if not sale_order.order_line:
                sale_order.unlink()
                raise UserError(_('No there lines in order'))
            self.message_post(
                body=_(
                    'Replenishment order created: <a href="/web'
                    '#id=%s&view_type=form&model=sale.order">%s</a><br/>'
                    'Total products: %s<br/>'
                    'Warehouse: %s') % (
                        sale_order.id, sale_order.name,
                        len(sale_order.order_line),
                        sale_order.warehouse_id.name),
                subject=_('New replenishment order'),
                message_type='notification')
            settings = self.env['res.config.settings']
            template = self.env.ref(
                'vending_machine.email_template_vending_machine_replenish')
            ctx = {
                'sale_order_name': sale_order.name,
                'email_to': settings.get_email_to_notify_replenishment(),
            }
            template.with_context(ctx).send_mail(self.id, force_send=True)

    def update_machine_stock(self, stock_data_array):
        if not stock_data_array:
            raise UserError(_('No stock data provided to update the machine.'))
        try:
            get_param = self.env['ir.config_parameter'].sudo().get_param
            param = 'vending_machine.jofemar_api_url'
            api_url = get_param(param, '')
            tz = timezone('Europe/Madrid')
            request_datetime = (datetime.datetime.now().astimezone(
                tz).strftime('%Y-%m-%d %H:%M:%S'))
            signature_str = (f'{self.company_id}{self.code}{request_datetime}'
                             f'{self.signature_key}')
            signature_hash = hashlib.sha1(signature_str.encode()).hexdigest()
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'xsd': 'http://www.w3.org/2001/XMLSchema',
            }
            jofemar_ns = 'http://compendia.jofemar.com/'
            envelope = ET.Element(
                '{http://schemas.xmlsoap.org/soap/envelope/}Envelope',
                nsmap=namespaces)
            body = ET.SubElement(
                envelope,
                '{http://schemas.xmlsoap.org/soap/envelope/}Body')
            set_stock_data = ET.SubElement(
                body, '{' + jofemar_ns + '}SetStockData')
            ET.SubElement(
                set_stock_data, '{' + jofemar_ns + '}CompanyId'
            ).text = self.company_id
            ET.SubElement(
                set_stock_data,
                '{' + jofemar_ns + '}MachineCode').text = str(self.code)
            stock_data_array_node = ET.SubElement(
                set_stock_data, '{' + jofemar_ns + '}StockDataArray')
            for product_data in stock_data_array:
                stock_data_item = ET.SubElement(
                    stock_data_array_node,
                    '{' + jofemar_ns + '}CpxType_SetStockData')
                ET.SubElement(
                    stock_data_item, '{' + jofemar_ns + '}SelectionNumber'
                ).text = str(product_data.get('SelectionNumber'))
                ET.SubElement(
                    stock_data_item, '{' + jofemar_ns + '}ProductCode'
                ).text = product_data.get('ProductCode')
                ET.SubElement(
                    stock_data_item, '{' + jofemar_ns + '}CurrentStock'
                ).text = str(product_data.get('CurrentStock'))
                ET.SubElement(
                    stock_data_item, '{' + jofemar_ns
                    + '}CurrentStockAsRelativeValue').text = 'true'
                ET.SubElement(
                    stock_data_item, '{' + jofemar_ns + '}DesiredStock'
                ).text = str(product_data.get('DesiredStock'))
            ET.SubElement(
                set_stock_data, '{' + jofemar_ns + '}RequestDateTime'
            ).text = request_datetime
            ET.SubElement(
                set_stock_data, '{' + jofemar_ns + '}Signature'
            ).text = signature_hash
            soap_request = ET.tostring(
                envelope, xml_declaration=True, encoding='utf-8')
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': '"http://compendia.jofemar.com/SetStockData"',
            }
            response = requests.post(
                api_url, data=soap_request, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            raise UserError(_('Connection error with Jofemar API: %s') % e)
        except ET.ParseError as e:
            raise UserError(_('XML parsing error from Jofemar API: %s') % e)
        except Exception as e:
            raise UserError(_(
                'An unexpected error occurred when calling Jofemar API: %s')
                % e)

    def update_machine_stock_with_move_lines(self, move_lines):
        stock_data_list = self._get_stock_data_from_api()
        StockDataArray = []
        for move in move_lines:
            default_code = move.product_id.default_code
            if move.product_id and default_code and move.quantity_done > 0:
                stock_data = list(filter(
                    lambda item: item.get('product_code') == default_code,
                    stock_data_list))
                if stock_data:
                    selection_number = stock_data[0].get('selection_number', '')
                    product_code = stock_data[0].get('product_code', '')
                    current_stock = int(move.quantity_done)
                    desired_stock = int(stock_data[0].get('stock_target', 0))
                    StockDataArray.append({
                        'SelectionNumber': selection_number,
                        'ProductCode': product_code,
                        'CurrentStock': current_stock,
                        'DesiredStock': desired_stock,
                    })
        self.update_machine_stock(StockDataArray)

    def action_replenish(self):
        self.ensure_one()
        view = self.env.ref(
            'vending_machine.vending_machine_replenish_confirm_view_form')
        return {
            'name': _('Confirm replenishment'),
            'res_model': 'vending.machine.replenish.confirm',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view.id,
            'target': 'new',
            'context': {
                'default_vending_machine_id': self.id,
            },
        }
