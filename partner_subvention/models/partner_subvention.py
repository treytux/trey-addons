###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PartnerSubvention(models.Model):
    _name = 'partner.subvention'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Partner subvention'

    name = fields.Char(
        string='Name',
        translate=True,
        required=True,
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company.id,
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    target = fields.Html(
        string='Target',
        translate=True,
        required=True,
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    dossier_code = fields.Char(
        string='Dossier code',
        required=True,
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    entity_subvention_id = fields.Many2one(
        comodel_name='res.partner',
        string='Entity granting the subvention',
        required=True,
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Beneficiary',
        required=True,
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    request_date = fields.Date(
        string='Request date',
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    grant_date = fields.Date(
        string='Grant date',
        tracking=True,
        copy=False,
    )
    agreement_date = fields.Date(
        string='Agreement date',
        tracking=True,
        copy=False,
    )
    start_project_date = fields.Date(
        string='Start project date',
        tracking=True,
    )
    end_project_date = fields.Date(
        string='End project date',
        tracking=True,
    )
    presentation_invoice_date = fields.Date(
        string='Presentation invoice date',
        tracking=True,
    )
    justification_date = fields.Date(
        string='Justification date',
        tracking=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    amount_requested = fields.Float(
        string='Amount requested',
        digits='Account',
        tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    amount_granted = fields.Float(
        string='Amount granted',
        digits='Account',
        required=True,
        tracking=True,
        copy=False,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('presented', 'Presented'),
            ('rectification', 'Rectification'),
            ('approved', 'Approved'),
            ('reformulated', 'Reformulated'),
            ('execution', 'In execution'),
            ('justification', 'In justification'),
            ('finished', 'Finished'),
            ('rejected', 'Rejected'),
        ],
        string='State',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )
    invoice_ids = fields.Many2many(
        comodel_name='account.move',
        relation='subvention_invoice_rel',
        column1='subvention_id',
        column2='invoice_id',
        string='Invoices',
        tracking=True,
        copy=False,
    )
    presented_file = fields.Binary(
        string='Presented file',
        tracking=True,
        copy=False,
    )
    approved_rejected_file = fields.Binary(
        string='Approved/rejected file',
        tracking=True,
        copy=False,
    )
    resolution_file = fields.Binary(
        string='Resolution file',
        tracking=True,
        copy=False,
    )
    justification_file = fields.Binary(
        string='Justification file',
        tracking=True,
        copy=False,
    )

    @api.constrains('amount_requested')
    def _check_amount_requested(self):
        if self.amount_requested <= 0:
            raise ValidationError(_('The amount requested must be positive.'))

    @api.constrains('dossier_code')
    def _check_dossier_code_unique(self):
        subvention_count = self.search_count([
            ('dossier_code', '=', self.dossier_code),
            ('id', '!=', self.id),
        ])
        if subvention_count >= 1:
            raise ValidationError(_(
                'There is already another partner subvention with this same '
                'dossier code: %s. It must be unique.') % self.dossier_code)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name=_("%s (copy)") % self.name)
        return super().copy(default)
