###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ConnectorSupplier(models.Model):
    _name = 'connector.supplier'
    _description = 'Connector supplier info base'

    name = fields.Char(
        string='Name',
        required=True,
    )
    username_ws = fields.Char(
        string='Username WS',
    )
    password_ws = fields.Char(
        string='Password WS',
    )
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        required=True,
    )
    supplier_mode = fields.Selection(
        selection=[],
        string='Supplier mode',
    )
