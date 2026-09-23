###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PartnerInfoData(models.Model):
    _name = 'partner.info.data'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Partner info data'

    name = fields.Char(
        default=lambda self: _('Info data'),
        translate=True,
    )
    biological_sex = fields.Char(
        string='Biological sex',
        required=True,
        tracking=True,
    )
    birthdate = fields.Date(
        string='Birthdate',
        required=True,
    )
    age = fields.Integer(
        string='Age',
        compute='_compute_age',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner user',
        required=True,
        help='Person who directly receives the services of the association.',
        tracking=True,
    )
    partner_ids = fields.Many2many(
        compute='_compute_partners_partner',
        string='Partners',
        comodel_name='res.partner',
        relation='partner2info_data_rel',
        column1='partner_id',
        column2='info_data_id',
        help=(
            'Partner/s of the user. To appear in the selection, they must '
            'be relations with other partner contacts marked as "Is partner '
            'full member?" or "Is partner collaborator?".'
        ),
        tracking=True,
    )
    family_ids = fields.Many2many(
        compute='_compute_family_partner',
        string='Family',
        comodel_name='res.partner',
        relation='family2info_data_rel',
        column1='family_id',
        column2='info_data_id',
        help=(
            'Family of the user. To appear in the selection, they must be '
            'relations with other partner contacts marked as "Is family?".'
        ),
        tracking=True,
    )
    diagnostic_professional_id = fields.Many2one(
        comodel_name='res.partner',
        string='Diagnostic professional',
        tracking=True,
    )
    job_profile = fields.Html(
        string='Job profile',
        tracking=True,
    )
    cv_file = fields.Binary(
        string='CV file',
        tracking=True,
    )
    protected_document_ids = fields.Many2many(
        string='Protected documents',
        comodel_name='partner.protected.document',
        relation='protected_document2info_data_rel',
        column1='protected_document_id',
        column2='info_data_id',
        tracking=True,
    )

    @api.depends(
        'partner_id', 'partner_id.is_partner_full_member',
        'partner_id.is_partner_collaborator')
    def _compute_partners_partner(self):
        for info_data in self:
            partners = info_data.partner_id.get_partners()
            if partners:
                info_data.partner_ids = [(6, 0, partners.ids)]

    @api.depends('partner_id', 'partner_id.is_family')
    def _compute_family_partner(self):
        for info_data in self:
            partners = info_data.partner_id.get_family()
            if partners:
                info_data.family_ids = [(6, 0, partners.ids)]

    @api.constrains('partner_id')
    def _check_partner_info_date_unique(self):
        for record in self:
            data = self.env['partner.info.data'].search_count([
                ('partner_id', '=', record.partner_id.id),
            ])
            if data > 1:
                raise ValidationError(
                    'There is already another record with the same partner.')

    @api.depends('birthdate')
    def _compute_age(self):
        for record in self:
            age = 0
            if record.birthdate:
                age = relativedelta(
                    fields.Date.today(), record.birthdate).years
            record.age = age

    def get_invoices(self, partner):
        return self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
        ])

    def get_project_tasks(self, partner):
        return self.env['project.task'].search([
            ('partner_id', '=', self.partner_id.id),
        ])

    def get_projects(self, partner):
        return self.env['project.task'].search([
            ('partner_id', '=', self.partner_id.id),
        ])

    def action_view_invoices(self):
        invoices = self.get_invoices(self.partner_id)
        form_view = self.env.ref('account.view_move_form')
        tree_view = self.env.ref('account.view_invoice_tree')
        search_view = self.env.ref('account.view_account_move_filter')
        action_vals = {
            'name': _('Invoices'),
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', invoices.ids)],
            'context': {
                'default_partner_id': self.partner_id.id,
            },
        }
        if len(invoices) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': invoices.ids[0],
            })
        return action_vals

    def action_view_events(self):
        tasks = self.get_project_tasks(self.partner_id)
        form_view = self.env.ref('project.view_task_form2')
        tree_view = self.env.ref('project.view_task_tree2')
        search_view = self.env.ref('project.view_task_search_form')
        action_vals = {
            'name': _('Events'),
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', tasks.ids)],
            'context': {
                'default_partner_id': self.partner_id.id,
            },
        }
        if len(tasks) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': tasks.ids[0],
            })
        return action_vals

    def action_view_projects(self):
        projects = self.get_projects(self.partner_id)
        form_view = self.env.ref('project.edit_project')
        tree_view = self.env.ref('project.view_project')
        search_view = self.env.ref('project.view_project_project_filter')
        action_vals = {
            'name': _('Projects'),
            'res_model': 'project.project',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', projects.ids)],
            'context': {
                'default_partner_id': self.partner_id.id,
            },
        }
        if len(projects) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': projects.ids[0],
            })
        return action_vals
