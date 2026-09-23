###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PartnerProtectedData(models.Model):
    _name = 'partner.protected.data'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Partner protected data'

    name = fields.Char(
        default=lambda self: _('Protected data'),
        translate=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner user',
        required=True,
        help='Person who directly receives the services of the association.',
        tracking=True,
    )
    diagnosis = fields.Binary(
        string='Diagnosis',
        tracking=True,
    )
    diagnosis_date = fields.Date(
        string='Diagnosis date',
        tracking=True,
    )
    disability_rate = fields.Float(
        string='Disability rate',
        tracking=True,
    )
    last_disability_date = fields.Date(
        string='Last disability date',
        tracking=True,
    )
    is_review = fields.Boolean(
        string='Is review',
        tracking=True,
    )
    review_date = fields.Date(
        string='Indicative review date',
        tracking=True,
    )
    mental_health_monitoring_team = fields.Char(
        string='Mental health monitoring team',
        tracking=True,
    )
    school_contact_id = fields.Many2one(
        comodel_name='res.partner',
        string='School contact',
        tracking=True,
    )
    academic_level = fields.Char(
        string='Academic level',
        tracking=True,
    )
    family_conflicts = fields.Html(
        string='Family conflicts',
        tracking=True,
    )
    external_diagnostic = fields.Binary(
        string='External diagnostic',
        tracking=True,
    )
    note = fields.Html(
        string='Note',
        tracking=True,
    )

    @api.constrains('partner_id')
    def _check_partner_protected_date_unique(self):
        for record in self:
            data = self.env['partner.protected.data'].search_count([
                ('partner_id', '=', record.partner_id.id),
            ])
            if data > 1:
                raise ValidationError(
                    'There is already another record with the same partner.')
