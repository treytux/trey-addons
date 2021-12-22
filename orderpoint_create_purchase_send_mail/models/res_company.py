###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    users_to_send_mail_ids = fields.Many2many(
        comodel_name='res.users',
        string='Users to notify',
        help='Users who will be notified of the creation of purchase order '
             'lines created from the stock warehouse orderpoint.'
    )
