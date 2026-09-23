###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmLeadRedFlag(models.Model):
    _name = 'crm.lead.red.flag'
    _description = 'Crm Lead Red Flag'

    name = fields.Char(
        string='Name',
        required=True,
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Red flag name already exists!"),
    ]
