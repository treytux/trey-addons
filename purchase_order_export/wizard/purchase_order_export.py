###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models, _
from io import BytesIO
import base64
import unicodecsv
try:
    import xlsxwriter
except ImportError:
    import logging
    _log = logging.getLogger(__name__)
    _log.debug('Can not import xlsxwriter`.')


class PurchaseOrderExport(models.TransientModel):
    _name = 'purchase.order.export'
    _description = 'Purchase order export'

    data = fields.Binary(
        string='Generated File',
        filter='*.csv',
    )
    name = fields.Char(
        string='File name',
        compute='_get_file_name',
    )
    format_file = fields.Selection(
        selection=[
            ('csv', 'CSV'),
            ('xls', 'Excel')],
        string='Format type',
        default='xls',
    )

    @api.multi
    def _get_file_name(self):
        self.name = _('purchase_order_%s.%s') % (
            fields.Datetime.now(), self.format_file)

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
            _('Taxes'): ', '.join([t.name for t in line.taxes_id]),
            _('Total'): line.price_subtotal
        } for line in order.order_line]

    @api.model
    def get_lines(self, orders):
        re = []
        for order in orders:
            header = self.get_purchase_order_header(order)
            lines = self.get_purchase_order_lines(order)
            re += [{**header, **line} for line in lines]
        return re

    @api.model
    def generate_xls(self, lines):
        with BytesIO() as ofile:
            workbook = xlsxwriter.Workbook(ofile, {})
            worksheet = workbook.add_worksheet(_('Purchases'))
            for col, data in enumerate(lines[0]):
                worksheet.write(0, col, data)
            for row, line in enumerate(lines):
                for col, data in enumerate(line):
                    worksheet.write(row + 1, col, line[data])
            workbook.close()
            ofile.seek(0)
            content = base64.encodestring(ofile.read())
        return content

    @api.model
    def generate_csv(self, lines):
        with BytesIO() as ofile:
            doc = unicodecsv.DictWriter(
                ofile, encoding='utf-8', fieldnames=lines[0].keys())
            doc.writeheader()
            for line in lines:
                doc.writerow(line)
            content = base64.encodestring(ofile.getvalue())
        return content

    @api.multi
    def button_accept(self):
        orders = self.env['purchase.order'].browse(
            self.env.context['active_ids'])
        lines = self.get_lines(orders)
        generate = getattr(self, 'generate_%s' % self.format_file)
        self.write({'data': generate(lines)})
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
