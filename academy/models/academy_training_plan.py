###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AcademyTrainingPlan(models.Model):
    _name = 'academy.training.plan'
    _description = 'Training Plan'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True,
    )
    short_name = fields.Char(
        string='Short name',
    )
    description = fields.Text(
        string='Description',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    start_date = fields.Date(
        string='Start date',
        required=True,
    )
    end_date = fields.Date(
        string='End date',
        required=True,
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('in_progress', 'In progress'),
            ('closed', 'Closed'),
        ],
        required=True,
        default='in_progress',
        tracking=True,
    )
    activity_ids = fields.One2many(
        comodel_name='academy.activity',
        inverse_name='training_plan_id',
        string='Lines',
    )
    typology_id = fields.Many2one(
        comodel_name='academy.typology',
        string='Typology',
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        required=True,
    )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for training_plan in self:
            if not training_plan.end_date or not training_plan.start_date:
                continue
            if training_plan.end_date < training_plan.start_date:
                raise ValidationError(
                    _('Start date cannot be later than the end date.'))
            if not training_plan.activity_ids:
                continue
            training_plan.activity_ids._check_dates()

    @api.model_create_multi
    def create(self, vals_list):
        plans = super().create(vals_list)
        account_analytic_model = self.env['account.analytic.account']
        plans_without_analytic = plans.filtered(
            lambda record: not record.analytic_account_id)
        for plan in plans_without_analytic:
            analytic_account = account_analytic_model.create({
                'name': plan.name,
                'company_id': plan.company_id.id,
                'plan_id': self.env.ref('academy.academy_analytic_plan').id,
            })
            plan.analytic_account_id = analytic_account
        return plans

    def write(self, vals):
        res = super().write(vals)
        if 'name' not in vals:
            for plan in self:
                if plan.analytic_account_id:
                    plan.analytic_account_id.name = plan.name
        return res

    def close_active_training_plans(self, training_plan_ids=None):
        today = fields.Date.today()
        domain = [
            '&', '&',
            ('active', '=', True),
            ('state', '=', 'in_progress'),
            ('end_date', '<', today),
        ]
        if training_plan_ids:
            domain = ['|', ('id', 'in', training_plan_ids.ids)] + domain
        plans_to_close = self.search(domain)
        if plans_to_close:
            plans_to_close.write({
                'state': 'closed',
                'active': False,
            })
            plans_future_end_date = plans_to_close.filtered(
                lambda p: p.end_date > today)
            if plans_future_end_date:
                plans_future_end_date.write({'end_date': today})
        return plans_to_close

    def to_closed(self):
        self.ensure_one()
        if not self.state == 'in_progress':
            return
        if self.activity_ids:
            enroll_obj = self.env['academy.enrollment']
            enroll_obj.finish_enrollments(self.activity_ids)
            self.activity_ids.close_active_activities(self)
            self.close_active_training_plans(self)
        self.state = 'closed'
        today = fields.Date.today()
        if self.end_date > today:
            self.end_date = today
