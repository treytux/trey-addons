###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmLeadObjection(models.Model):
    _name = 'crm.lead.objection'
    _description = 'Objections of the leads'

    name = fields.Char(
        required=True,
    )
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Objection name already exists!"),
    ]
