###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import io
import json

from odoo import http
from odoo.http import request
from odoo.tools.misc import xlwt


class CustomTableExporter(http.Controller):

    @http.route('/web/pivot/export_custom_xls', type='http', auth='user')
    def export_xls(self, data, token):
        jdata = json.loads(data)
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(
            jdata.get('title', 'Pivot')[:31], cell_overwrite_ok=True
        )
        header_bold = xlwt.easyxf(
            'font: bold on; pattern: pattern solid, \
            fore_colour gray25; align: horiz center;'
        )
        header_plain = xlwt.easyxf('pattern: pattern solid, fore_colour gray25;')
        bold = xlwt.easyxf('font: bold on;')
        style_decimal = xlwt.easyxf(num_format_str='#,##0.00')
        style_decimal_bold = xlwt.easyxf(
            'font: bold on;', num_format_str='#,##0.00')
        headers = jdata.get('headers', [])
        for i, header_row in enumerate(headers):
            x = 1
            for header in header_row:
                title = header.get('title', '')
                width = header.get('width', 1)
                height = header.get('height', 1)
                if width > 1 or height > 1:
                    worksheet.write_merge(
                        i, i + height - 1, x, x + width - 1, title, header_bold)
                else:
                    worksheet.write(i, x, title, header_bold)
                x += width
        y = len(headers)
        measure_row = jdata.get('measure_row', [])
        worksheet.write(y, 0, '', header_plain)
        for x, measure in enumerate(measure_row, 1):
            title = (
                measure.get('measure', measure)
                if isinstance(measure, dict)
                else measure)
            worksheet.write(y, x, title, header_bold)
        y += 1
        for row in jdata.get('rows', []):
            worksheet.write(y, 0, row.get('title', ''))
            for x, cell in enumerate(row.get('values', []), 1):
                val = cell.get('value')
                if isinstance(val, str) and val.startswith('='):
                    try:
                        val = xlwt.Formula(val[1:])
                        style = (
                            style_decimal_bold
                            if cell.get('is_bold')
                            else style_decimal)
                    except Exception:
                        style = (
                            bold
                            if cell.get('is_bold')
                            else xlwt.Style.default_style)
                else:
                    style = (
                        bold
                        if cell.get('is_bold')
                        else xlwt.Style.default_style)
                worksheet.write(y, x, val, style)
            y += 1
        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        return request.make_response(
            fp.read(),
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=sales.xls'),
            ],
            cookies={'fileToken': token})
