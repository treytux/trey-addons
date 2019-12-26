# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields
from openerp import SUPERUSER_ID


class ResCompany(models.Model):
    _inherit = "res.company"

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        help='Default user for edi documents',
        default=SUPERUSER_ID)
    in_path = fields.Char(
        string='In path')
    out_path = fields.Char(
        string='Out path')
    duplicated_path = fields.Char(
        string='Duplicated path')
