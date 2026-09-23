# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api
from ..models.ede_api import Ede


class ResCompany(models.Model):
    _inherit = 'res.company'

    ede_supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='E/D/E Supplier',
        domain=[('supplier', '=', True)],
        required=False,
    )
    ede_picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Picking Type Name',
        domain=[('code', '=', 'incoming')],
        required=False,
    )
    ede_user_id = fields.Many2one(
        comodel_name='res.users',
        string='User Notification',
    )
    ede_runtime = fields.Selection(
        string='Runtime',
        selection=[('test', 'Test'),
                   ('real', 'Real'),
                   ],
        default='test',
    )
    ede_test_wsdl = fields.Char(
        string='Wsdl Url',
    )
    ede_test_member = fields.Char(
        string='Member Id',
    )
    ede_test_user = fields.Char(
        string='User',
    )
    ede_test_password = fields.Char(
        string='Password',
    )
    ede_test_url_user = fields.Char(
        string='Url User',
    )
    ede_test_url_password = fields.Char(
        string='Url Password',
    )
    ede_real_wsdl = fields.Char(
        string='Wsdl',
    )
    ede_real_member = fields.Char(
        string='Member Id',
    )
    ede_real_user = fields.Char(
        string='User',
    )
    ede_real_password = fields.Char(
        string='Password',
    )
    ede_real_url_user = fields.Char(
        string='Url User',
    )
    ede_real_url_password = fields.Char(
        string='Url Password',
    )

    @api.model
    def ede_client(self):
        if self.ede_runtime == 'test':
            return Ede(
                wsdl=self.ede_test_wsdl,
                member=self.ede_test_member,
                user=self.ede_test_user,
                password=self.ede_test_password,
                url_user=self.ede_test_url_user,
                url_password=self.ede_test_url_password
            )
        else:
            return Ede(
                wsdl=self.ede_real_wsdl,
                member=self.ede_real_member,
                user=self.ede_real_user,
                password=self.ede_real_password,
                url_user=self.ede_real_url_user,
                url_password=self.ede_real_url_password
            )

    @api.model
    def ede_credentials(self):
        if self.ede_runtime == 'test':
            return {
                'MemberId': self.ede_test_member,
                'Login': self.ede_test_user,
                'Password': self.ede_test_password,
            }
        else:
            return {
                'MemberId': self.ede_real_member,
                'Login': self.ede_real_user,
                'Password': self.ede_real_password,
            }
