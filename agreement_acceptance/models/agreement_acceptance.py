###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AgreementAcceptance(models.Model):
    _name = 'agreement.acceptance'
    _description = 'Agreement Acceptance'

    name = fields.Char(
        related='agreement_template.name',
    )
    agreement_template = fields.Many2one(
        comodel_name='agreement.template',
        string='Agreement Template',
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('accepted', 'Accepted'),
            ('unaccepted', 'Unaccepted'),
        ],
        string='State',
        help='Document Status',
        default='unaccepted',
    )
    acceptance_date = fields.Date(
        string='Acceptance Date',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        domain='[("is_company","=",True)]',
        required=True,
    )
    acceptance_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Acceptance contact',
        domain='[("is_company","=",False),("parent_id","=",partner_id)]',
    )
    custom_document = fields.Binary(
        string='Custom Document',
        help='File that will contain the customization of the agreement',
    )
