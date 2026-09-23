###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    is_partner_typology = fields.Boolean(
        string='Is Partner Typology',
        help='If enabled, this category can be selected as a partner typology '
             'and used to calculate planned hours targets.',
    )
    min_planned_rate = fields.Float(
        string='Minimum Planned Rate',
        help='Minimum completion rate expected over planned hours.',
    )
    max_planned_rate = fields.Float(
        string='Maximum Planned Rate',
        help='Maximum completion rate expected over planned hours.',
    )

    @api.constrains(
        'is_partner_typology',
        'min_planned_rate',
        'max_planned_rate')
    def _check_partner_typology_planned_rates(self):
        for category in self.filtered('is_partner_typology'):
            if (
                    category.min_planned_rate < 0.0
                    or category.max_planned_rate < 0.0):
                raise ValidationError(_('Planned rates cannot be negative.'))
            if category.min_planned_rate > category.max_planned_rate:
                raise ValidationError(_(
                    'The minimum planned rate must be lower than or equal to '
                    'the maximum planned rate.'))
