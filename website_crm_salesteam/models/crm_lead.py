###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def website_form_input_filter(self, request, values):
        values = super().website_form_input_filter(request, values)
        website = request.website
        if 'salesteam_id' in website._fields and website.salesteam_id:
            values['team_id'] = website.salesteam_id.id
        return values
