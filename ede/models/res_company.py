###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons.ede.models.ede_api import EdeApi
from odoo.addons.ede.models.ede_ftp import EdeFTP


class ResCompany(models.Model):
    _inherit = 'res.company'

    ede_supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='E/D/E Supplier',
        domain=[('supplier', '=', True)],
    )
    ede_picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Picking Type Name',
        domain=[('code', '=', 'incoming')],
    )
    ede_user_id = fields.Many2one(
        comodel_name='res.users',
        string='User Notification',
    )
    ede_runtime = fields.Selection(
        string='Runtime',
        selection=[
            ('test', 'Test'),
            ('real', 'Real'),
        ],
        default='test',
    )
    ede_test_wsdl = fields.Char(
        string='Test Wsdl',
    )
    ede_test_member = fields.Char(
        string='Test Member Id',
    )
    ede_test_user = fields.Char(
        string='Test User',
    )
    ede_test_password = fields.Char(
        string='Test Password',
    )
    ede_test_url_user = fields.Char(
        string='Test Url User',
    )
    ede_test_url_password = fields.Char(
        string='Test Url Password',
    )
    ede_real_wsdl = fields.Char(
        string='Real Wsdl',
    )
    ede_real_member = fields.Char(
        string='Real Member Id',
    )
    ede_real_user = fields.Char(
        string='Real User',
    )
    ede_real_password = fields.Char(
        string='Real Password',
    )
    ede_real_url_user = fields.Char(
        string='Real Url User',
    )
    ede_real_url_password = fields.Char(
        string='Real Url Password',
    )
    ede_start_code = fields.Char(
        string='Ede Start Code',
    )
    ede_use_ftp = fields.Boolean(
        string='Use ede FTP',
    )
    ede_ftp_host = fields.Char(
        string='Host',
        defaul='ftp4.ede.de',
    )
    ede_ftp_user = fields.Char(
        string='User',
    )
    ede_ftp_pass = fields.Char(
        string='Password',
    )
    ede_ftp_remote_path = fields.Char(
        string='Remote path',
    )
    ede_ftp_local_path = fields.Char(
        string='Local path',
    )
    ede_user_notify = fields.Many2many(
        comodel_name='res.users',
        string='User notify',
    )
    ede_delete_done = fields.Boolean(
        string='Delete done file?',
    )
    ede_confirm_draft_invoice = fields.Boolean(
        string='Confirm draft invoice?',
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Purchase journal',
        domain=[('type', '=', 'purchase')],
    )

    @api.model
    def ede_client(self):
        if self.ede_runtime == 'test':
            return EdeApi(
                wsdl=self.ede_test_wsdl,
                member=self.ede_test_member,
                user=self.ede_test_user,
                password=self.ede_test_password,
                url_user=self.ede_test_url_user,
                url_password=self.ede_test_url_password
            )
        return EdeApi(
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
        return {
            'MemberId': self.ede_real_member,
            'Login': self.ede_real_user,
            'Password': self.ede_real_password,
        }

    @api.model
    def ede_ftp(self):
        return EdeFTP(
            host=self.ede_ftp_host, user=self.ede_ftp_user,
            password=self.ede_ftp_pass,
            local_path=self.ede_ftp_local_path,
            remote_path=self.ede_ftp_remote_path,
            user_notify=self.ede_user_notify,
        )
