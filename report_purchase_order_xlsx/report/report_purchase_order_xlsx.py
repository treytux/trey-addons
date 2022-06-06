###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class ReportPurchaseOrderXlsx(models.AbstractModel):
    _name = 'report.report_xlsx.purchase_order_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def get_lang(self, user_id):
        lang_code = self.env['res.users'].browse(user_id).lang
        return self.env['res.lang']._lang_get(lang_code)

    def set_header_report_purchase_order_xlsx(self, sheet, title_format):
        sheet.write('A1', _('Nº Purchase'), title_format)
        sheet.write('B1', _('Reference'), title_format)
        sheet.write('C1', _('Partner'), title_format)
        sheet.write('D1', _('Street'), title_format)
        sheet.write('E1', _('Zip'), title_format)
        sheet.write('F1', _('City'), title_format)
        sheet.write('G1', _('Phone'), title_format)
        sheet.write('H1', _('Date order'), title_format)
        sheet.write('I1', _('Barcode'), title_format)
        sheet.write('J1', _('Default code'), title_format)
        sheet.write('K1', _('Product'), title_format)
        sheet.write('L1', _('Product quantity'), title_format)
        sheet.write('M1', _('Download date'), title_format)

    def create_line_workbook(
            self, sheet, position, line, date_format, order=None):
        sheet.write('A' + str(position), line.order_id.name)
        sheet.write('B' + str(position), (
            line.sale_order_id and line.sale_order_id.team_id.id
            or order and order.team_id.id or ''))
        sheet.write('C' + str(position), (
            line.sale_order_id and line.sale_order_id.partner_id.name
            or order and order.partner_id.name or ''))
        street = (
            line.sale_order_id and line.sale_order_id.partner_id.street
            or order and order.partner_id.street or '')
        street2 = (
            line.sale_order_id and line.sale_order_id.partner_id.street2
            or order and order.partner_id.street2 or '')
        sheet.write('D' + str(position), street + ' ' + street2)
        sheet.write('E' + str(position), (
            line.sale_order_id and line.sale_order_id.partner_id.zip
            or order and order.partner_id.zip or ''))
        sheet.write('F' + str(position), (
            line.sale_order_id and line.sale_order_id.partner_id.city
            or order and order.partner_id.city or ''))
        sheet.write('G' + str(position), (
            line.sale_order_id and line.sale_order_id.partner_id.phone
            or order and order.partner_id.phone or ''))
        sheet.write('H' + str(position), line.order_id.date_order, date_format)
        sheet.write('I' + str(position), line.product_id.barcode or '')
        sheet.write('J' + str(position), line.product_id.default_code or '')
        sheet.write('K' + str(position), line.product_id.name)
        sheet.write('L' + str(position), line.product_qty)
        sheet.write('M' + str(position), fields.Datetime.now(), date_format)

    def set_columns_report_purchase_order(self, sheet):
        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 25)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 25)
        sheet.set_column('I:I', 20)
        sheet.set_column('J:J', 20)
        sheet.set_column('K:K', 20)
        sheet.set_column('L:L', 20)
        sheet.set_column('M:M', 25)

    def generate_xlsx_report(self, workbook, data, purchase_orders):
        title_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vjustify',
        })
        lang = self.get_lang(self.env.user.id)
        date_format = lang.date_format.replace('%d', 'dd')
        date_format = date_format.replace('%m', 'mm')
        date_format = date_format.replace('%Y', 'YYYY')
        date_format = date_format.replace('/', '-')
        date_format = workbook.add_format({
            'num_format': date_format,
        })
        sheet = workbook.add_worksheet(_('Purchase orders'))
        self.set_columns_report_purchase_order(sheet)
        self.set_header_report_purchase_order_xlsx(sheet, title_format)
        purchase_order_lines = purchase_orders.mapped('order_line')
        row = 2
        for obj in purchase_order_lines:
            fill_line = False
            if obj.sale_order_id:
                self.create_line_workbook(sheet, row, obj, date_format)
                row += 1
            else:
                sale_order_ids = self.env['purchase.order'].get_sale_order_ids(
                    obj.order_id)
                for sale in sale_order_ids:
                    sale_order = self.env['sale.order'].browse(sale)
                    if obj.product_id.barcode in sale_order.mapped(
                            'order_line.product_id.barcode'):
                        fill_line = True
                        self.create_line_workbook(
                            sheet, row, obj, date_format, sale_order)
                        row += 1
                if not fill_line:
                    self.create_line_workbook(sheet, row, obj, date_format)
                    row += 1
