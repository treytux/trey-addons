###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields
import datetime
from dateutil.relativedelta import relativedelta


class Users(models.Model):
    _inherit = 'res.users'

    last_sale_date = fields.Datetime(
        comodel_name='sale.order',
        string='Last Sale Order',
        compute='_compute_last_sale_date')

    @api.one
    @api.depends('partner_id')
    def _compute_last_sale_date(self):
        last_sale_id = self.env['sale.order'].search([
            ('partner_id', 'in', [
                self.partner_id.id, self.partner_id.commercial_partner_id.id]),
            ('state', 'in', ['sale', 'done'])],
            order='confirmation_date desc', limit=1)
        self.last_sale_date = (
            last_sale_id and
            last_sale_id.confirmation_date or None)

    @api.multi
    def block_users_by_sale_inactivity(self):
        for user in self:
            user.partner_id.allowed = False

    @api.model
    def cron_block_users_by_sale_inactivity(self):
        now = datetime.datetime.now()
        inactive_days = self.env['res.config.settings'].search(
            [], order='id desc', limit=1).sale_inactive_days
        inactive_date = fields.Datetime.to_string(
            now - relativedelta(days=inactive_days))
        users = self.with_context(cron=True).search([
            ('share', '=', True), ('last_sale_date', '<=', inactive_date)])
        users.block_users_by_sale_inactivity()
