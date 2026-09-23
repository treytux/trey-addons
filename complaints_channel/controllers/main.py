###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import _
from odoo.http import request, route
from werkzeug import utils

try:
    from odoo.addons.portal.controllers.portal import CustomerPortal
except ImportError:
    CustomerPortal = object
try:
    from odoo.addons.account.controllers.portal import PortalAccount
except ImportError:
    PortalAccount = object


class CustomerPortal(CustomerPortal):

    def get_companies(self):
        return request.env['res.company'].sudo().search([])

    @route('/complaints_channel/complaint',
           type='http',
           auth='public',
           website=True,)
    def complaints_form(self, anonymous=None, employee=None, first_name=None,
                        last_name=None, email=None, phone=None, company_id=None,
                        working_location=None, department=None,
                        people_involved=None, witnesses=None,
                        reportable_facts=None, date_start=None, date_end=None,
                        evidence_description=None, evidence_file=None,
                        csrf_token=None, **kw):
        values = {}
        companies = self.get_companies()
        if len(companies) > 1:
            values['companies'] = self.get_companies()
        else:
            values['company'] = companies
        msg = kw.get('msg', False)
        if msg:
            if msg == '1':
                values['msg'] = _('Complaint was sent successfully')
            if msg == '2':
                values['error'] = _('Complaint was not created due an error')
        if request.httprequest.method != "POST":
            return request.render(
                'complaints_channel.complaint_form', values)
        else:
            vals = {
                'email': email,
                'people_involved': people_involved,
                'witnesses': witnesses,
                'reportable_facts': reportable_facts,
                'company': int(company_id),
                'start_date': date_start,
                'description': evidence_description,
                'is_anonymous': anonymous,
                'is_employee': employee,
                'name': first_name,
                'phone': phone,
                'last_name': last_name,
                'work_location': working_location,
                'department': department,
                'date_end': date_end != '' and date_end or None,
            }
            if evidence_file:
                evidence_file_datas = evidence_file.read()
                vals['evidence_filename'] = evidence_file.filename
                vals['evidence_file'] = base64.b64encode(evidence_file_datas)
            request.env['complaints.channel'].sudo().create(vals)
            return utils.redirect('/complaints_channel/complaint?msg=1')
