###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, models, fields


class Users(models.Model):
    _inherit = 'res.users'

    @api.multi
    def block_users_by_inactivity(self):
        for user in self:
            user.partner_id.allowed = False

    @api.model
    def cron_block_users_by_inactivity(self):
        now = datetime.datetime.now()
        inactive_days = self.env['res.config.settings'].search(
            [], order='id desc', limit=1).user_inactive_days
        inactive_date = fields.Datetime.to_string(
            now - relativedelta(days=inactive_days))
        users = self.with_context(cron=True).search([
            ('share', '=', True), ('login_date', '<', inactive_date)])
        users.block_users_by_inactivity()
