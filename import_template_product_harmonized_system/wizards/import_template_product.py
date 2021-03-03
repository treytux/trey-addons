###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ImportTemplateProduct(models.TransientModel):
    _inherit = 'import.template.product'

    def parse_float(self, value):
        try:
            return int(value)
        except Exception:
            return value

    def hs_code_id_get_or_create(self, name):
        errors = []
        if not name:
            return None, errors
        name = self.parse_float(name)
        hs_codes = self.env['hs.code'].search([
            ('local_code', '=', name)
        ])
        if len(hs_codes) > 1:
            errors.append(_(
                'More than one HS code found for local code %s.') % name)
        if not hs_codes:
            errors.append(_(
                'The HS code with local code \'%s\' does not exist, select '
                'one of the available ones.') % name)
            return None, errors
        return hs_codes[0].id, errors

    def origin_country_id_get_or_create(self, name):
        errors = []
        if not name:
            return None, errors
        countries = self.env['res.country'].search([
            ('name', '=', name)
        ])
        if len(countries) > 1:
            errors.append(_(
                'More than one country found for %s.') % name)
        if not countries:
            errors.append(_(
                'The country \'%s\' does not exist, select one of the '
                'available ones.') % name)
            return None, errors
        return countries[0].id, errors
