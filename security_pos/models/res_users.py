###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    pos_config_ids = fields.Many2many(
        string='Pos configs',
        comodel_name='pos.config',
        relation='user_pos_config_rel',
        column1='user_id',
        column2='pos_config_id',
        help='TPVs allowed for this user.',
    )
