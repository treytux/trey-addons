###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ComplaintChannel(models.Model):
    _name = 'complaints.channel'
    _description = 'Complaint channel'

    is_anonymous = fields.Boolean(
        string='Anonymous',
    )
    is_employee = fields.Boolean(
        string='Employee',
    )
    name = fields.Char(
        string='Name',
    )
    last_name = fields.Char(
        string='Last name',
    )
    email = fields.Char(
        string='Email',
        required=True,
    )
    phone = fields.Char(
        string='Phone',
    )
    company = fields.Many2one(
        comodel_name='res.company',
        required=True,
    )
    work_location = fields.Char(
        string='Work location',
    )
    department = fields.Char(
        string='Department',
    )
    people_involved = fields.Char(
        string='People involved',
        required=True,
    )
    witnesses = fields.Char(
        string='Witnesses',
        required=True,
    )
    reportable_facts = fields.Char(
        string="Reportable facts",
        required=True,
    )
    start_date = fields.Date(
        string='Start date',
        required=True,
    )
    date_end = fields.Date(
        string='End date',
    )
    description = fields.Text(
        string='Description',
        required=True,
    )
    evidence_filename = fields.Char(
        string='Filename',
    )
    evidence_file = fields.Binary(
        string='File',
        attachment=True,
    )
