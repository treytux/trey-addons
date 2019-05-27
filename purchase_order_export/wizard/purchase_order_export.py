###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models, _
from io import BytesIO
import base64
import unicodecsv


class PurchaseOrderExport(models.TransientModel):
    _name = 'purchase.order.export'
    _description = 'Purchase order export'

    data = fields.Binary(
        string='Generated File',
        filter='*.csv')
    name = fields.Char(
        string='File name',
        compute='_get_file_name')

    @api.multi
    def _get_file_name(self):
        self.name = _('purchase_order_%s.csv') % fields.Datetime.now()

    @api.model
    def get_purchase_order_header(self, order):
        send_to = order.picking_type_id
        return {
            _('Purchase order'): order.name,
            _('Date'): order.date_order,
            _('Supplier number'): order.partner_id.ref,
            _('Name'): order.partner_id.name,
            _('Address'): order.partner_id.contact_address or '',
            _('Email'): order.partner_id.email or '',
            _('Currency'): order.currency_id.name,
            _('Send to'): (
                send_to.warehouse_id and
                send_to.warehouse_id.partner_id.contact_address or
                send_to.name)}

    @api.model
    def get_purchase_order_lines(self, order):
        return [{
            _('Description'): line.name,
            _('Quantity'): line.price_unit,
            _('Price Unit'): line.product_qty,
            _('Price Tax'): line.price_tax,
            _('Taxes'): [t.name for t in line.taxes_id],
            _('Total'): line.price_subtotal
        } for line in order.order_line]

    @api.model
    def export_purchase_orders(self, orders):
        re = []
        for order in orders:
            header = self.get_purchase_order_header(order)
            lines = self.get_purchase_order_lines(order)
            re += [{**header, **line} for line in lines]
        return re

    @api.multi
    def button_accept(self):
        orders = self.env['purchase.order'].browse(
            self.env.context['active_ids'])
        with BytesIO() as ofile:
            data = self.export_purchase_orders(orders)
            doc = unicodecsv.DictWriter(
                ofile, encoding='utf-8', fieldnames=data[0].keys())
            doc.writeheader()
            for line in data:
                doc.writerow(line)
            content = base64.encodestring(ofile.getvalue())
        self.write({'data': content})
        res = self.env['ir.model.data'].get_object_reference(
            'purchase_order_export',
            'purchase_order_export_ok_form')
        return {
            'name': _('Purchase order export'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res and res[1] or False],
            'res_model': 'purchase.order.export',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new'}
