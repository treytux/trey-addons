# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    report_header = fields.Text(
        string='Report header',
        company_dependent=True)
    report_header_readonly = fields.Text(
        string='Report header',
        related='report_header',
        readonly=True)
    custom_header = fields.Boolean(
        string='Custom header',
        help='Check this to define the report header manually. Otherwise it '
             'will be filled in automatically.')

    def onchange_header(self, cr, uid, ids, custom_header, name, street,
                        street2, zip, city, state_id, country_id, vat,
                        context=None):
        if custom_header:
            return {}

        state_name = None
        if state_id:
            state_obj = self.pool.get('res.country.state')
            state = state_obj.browse(cr, uid, state_id, context=context)
            if state:
                state_name = state.name

        country_name = None
        if country_id:
            country_obj = self.pool.get('res.country')
            country = country_obj.browse(cr, uid, country_id, context=context)
            if country:
                country_name = country.name

        res = '<br/>'.join(filter(bool, [
            name and '%s' % name,
            street and '%s' % street,
            street2 and '%s' % street2,
            zip and '%s%s%s' % (
                zip,
                ', %s' % city if city else '',
                ' (%s)' % state_name if state_name else ''),
            country_name and '%s' % country_name,
            vat and '%s' % vat,
        ]))

        return {'value': {'report_header': res, 'report_header_readonly': res}}
