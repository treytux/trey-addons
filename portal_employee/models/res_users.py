###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    employee_portal_block_backoffice = fields.Boolean(
        string='Block backoffice access',
    )
    knowledge_categories = fields.Many2many(
        string='Knowledge categories',
        comodel_name='document.page',
        relation='res_users2document_page_rel',
        column1='document_page_id',
        column2='user_id',
        help='Documents in added categories will be shown for this user.',
    )
