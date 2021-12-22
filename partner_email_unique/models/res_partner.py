###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    email = fields.Char(
        copy=False,
    )

    @api.constrains('email', 'company_id')
    def _check_email_unique(self):
        for partner in self:
            if not partner.email:
                continue
            partner_count = self.env['res.partner'].sudo().search_count([
                ('email', '=', partner.email),
                ('id', '!=', partner.id),
                '|',
                ('company_id', '=', False),
                ('company_id', '=', partner.company_id.id),
                '|',
                ('active', '=', True),
                ('active', '=', False),
            ])
            if partner_count:
                raise ValidationError(_(
                    'The email %s already exists in another partner. '
                    'NOTE: This partner may be archived.') % partner.email)
