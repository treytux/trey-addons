###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons.termoclub.models.termoclub_api import TermoClubApi


class ResCompany(models.Model):
    _inherit = 'res.company'

    termoclub_supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        domain=[('supplier', '=', True)],
    )
    termoclub_wsdl = fields.Char(
        string='URL',
        default='http://compras.termoclub.com:8001/WSPedidos/Gestion.asmx'
                '?WSDL',
    )
    termoclub_user = fields.Char(
        string='User',
    )
    termoclub_password = fields.Char(
        string='Password',
    )
    termoclub_order_sent_type = fields.Selection(
        string='Sent type',
        selection=[
            ('manual', 'Manual'),
            ('automatic', 'automatic'),
        ],
        default='manual',
    )

    @api.model
    def termoclub_client(self):
        return TermoClubApi(
            wsdl=self.termoclub_wsdl,
            user=self.termoclub_user,
            password=self.termoclub_password,
        )
