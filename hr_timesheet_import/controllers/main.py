###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import http
from odoo.http import request


class HrTimesheetImport(http.Controller):
    @http.route(['/hr_timesheet/import'], type='json', auth='user')
    def hr_timesheet_sheet_import(self, **kw):
        info = json.loads(request.httprequest.data)
        result = request.env['hr_timesheet.sheet'].sudo().import_timesheet(
            info)
        return json.dumps({'result': result})
