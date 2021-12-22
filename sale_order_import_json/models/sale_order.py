###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json

from odoo import _, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def create_with_onchange(self, record, values):
        onchange_specs = {
            field_name: '1' for field_name, field in record._fields.items()
        }
        new = record.new(values)
        new._origin = None
        res = {'value': {}, 'warnings': set()}
        for field in record._onchange_spec():
            if onchange_specs.get(field):
                new._onchange_eval(field, onchange_specs[field], res)
        cache = record._convert_to_write(new._cache)
        cache.update(values)
        return record.create(cache)

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

        partners = partner_get_or_create(json_content['partner'])
        json_content['partner_id'] = partners.id
        if json_content.get('partner_shipping', False):
            partners = partner_get_or_create(json_content['partner_shipping'])
            json_content['partner_shipping_id'] = partners.id
        data = clean_content(self.env['sale.order'], json_content, ['state'])
        if json_content.get('team_name', False):
            team = get_crm_team(json_content['team_name'])
            data.update({
                'team_id': team.id,
            })
        sale = self.create_with_onchange(self.env['sale.order'], data)
        sale_line_obj = self.env['sale.order.line']
        for line in json_content['order_line']:
            products = self.env['product.product'].search([
                '|',
                ('default_code', '=', line['default_code']),
                ('barcode', '=', line['default_code']),
            ])
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
            self.create_with_onchange(sale_line_obj, data)
        content = json.dumps(str(json_content))
        self.env['ir.attachment'].create({
            'name': 'JSON_%s' % sale.name,
            'datas': base64.b64encode(content.encode()),
            'datas_fname': 'json_%s.json' % sale.name,
            'res_model': 'sale.order',
            'res_id': sale.id,
            'mimetype': 'application/json',
        })
        if json_content['state'] == 'confirmed':
            sale.action_confirm()
            for picking in sale.picking_ids:
                picking.action_confirm()
                picking.action_assign()
                for move in picking.move_lines:
                    move.quantity_done = move.product_uom_qty
                picking.action_done()
            sale.action_invoice_create()
            for invoice in sale.invoice_ids:
                invoice.date_invoice = json_content['invoice_date']
                invoice.action_invoice_open()
                payment_method = get_payment_method(
                    json_content['payment_method_name'])
                journal = invoice.journal_id
                if json_content.get('journal_name', False):
                    journal = get_journal(json_content['journal_name'])
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
