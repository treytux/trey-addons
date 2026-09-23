from odoo import _, api, fields, models


class AcademyActivity(models.Model):
    _inherit = 'academy.activity'

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

    def close_active_activities(self, plan_ids):
        activity_ids = super().close_active_activities(plan_ids)
        for activity in activity_ids:
            activity.visible_website = False
        return activity_ids
