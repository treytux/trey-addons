###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.addons import decimal_precision as dp


class ResCompany(models.Model):
    _inherit = 'res.company'

    margin_limit = fields.Float(
        string='Minimun margin limit per sale order line (%)',
        digits=dp.get_precision('Product Price'),
    )
    notification_method = fields.Selection(
        selection=[
            ('team_manager', 'Sales team manager'),
            ('user_unique', 'Unique user'),
        ],
        default='team_manager',
        string='Margin limit notification method',
        help='The team leader of the sales order team or an internal user of '
             'the company is notified. If you select "Unique user" you will '
             'have to fill in the field "User to notify"',
    )
    notification_user = fields.Many2one(
        comodel_name='res.users',
        required=True,
        string='User to notify',
        help='User notified when the method is "Unique user". Also used in'
             'case the order does not have a sales team or the sales team '
             'does not have a leader.',
    )
    include_delivery_lines = fields.Boolean(
        string='Include shipping lanes for margin limit calculation.',
    )
