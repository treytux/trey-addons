from odoo import _, api, fields, models


class AcademyTrainingPlan(models.Model):
    _inherit = 'academy.training.plan'

    visible_website = fields.Boolean(
        string='Visible on website',
        tracking=True,
    )

    website_status_text = fields.Char(
        string='On website',
        compute='_compute_website_status',
    )

    def change_website_visibility(self):
        for activity in self:
            activity.visible_website = not activity.visible_website

    @api.depends('visible_website')
    def _compute_website_status(self):
        for record in self:
            if record.visible_website:
                record.website_status_text = _('Published')
            else:
                record.website_status_text = _('Not Published')

    def close_active_training_plans(self):
        training_plan_ids = super().close_active_training_plans()
        for training_plan in training_plan_ids:
            training_plan.visible_website = False
        return training_plan_ids
