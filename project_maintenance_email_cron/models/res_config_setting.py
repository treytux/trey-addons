###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    email_cron = fields.Many2one(
        comodel_name='res.partner',
        string='Maintenance To: ',
    )

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('project_project.email_cron', self.email_cron.id)

    def get_values(self):
        res = super().get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        email = config_parameter.get_param('project_project.email_cron')
        email = int(email)
        if email == 0:
            email = False
        res.update(email_cron=email)
        return res
