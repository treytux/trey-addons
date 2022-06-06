###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _default_carrier_id(self):
        return self.env['delivery.carrier'].search([], limit=1)

    @api.model
    def _default_payment_mode_id(self):
        return self.env['account.payment.mode'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)

    @api.model
    def _default_journal_sale_id(self):
        return self.env['account.journal'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'sale'),
        ], limit=1)

    @api.model
    def _default_partner_account_id(self):
        return self.env['account.account'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('user_type_id', '=', self.env.ref(
                'account.data_account_type_receivable').id),
        ], limit=1)

    @api.model
    def _default_shipping_product_id(self):
        return self.env['product.product'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'service'),
        ], limit=1)

    @api.model
    def _default_journal_payment_id(self):
        return self.env['account.journal'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('type', 'in', ['bank', 'cash']),
        ], limit=1)

    @api.model
    def _default_fiscal_position_id(self):
        return self.env['account.fiscal.position'].search([
            '|',
            ('company_id', '=', None),
            ('company_id', '=', self.env.user.company_id.id),
            ('country_id', '=', self.env.user.country_id.id),
        ], limit=1)

    @api.model
    def _get_beezup_partner_account_id_domain(self):
        return [('user_type_id', '=', self.env.ref(
            'account.data_account_type_receivable').id)]

    beezup_product_ids2delete = fields.Text(
        string='Product ids to delete file',
        help='Internal field to store the ids of the unlinked products to '
             'delete them from the Bezzup file when it is updated.',
    )
    beezup_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Beezup pricelist',
        required=True,
        help='Pricelist used for Beezup connector pricing calculation.',
        default=lambda self: self.env.ref('product.list0'),
    )
    beezup_domain = fields.Text(
        string='Beezup domain',
        help='Internal field to store Beezup domain to connect.',
    )
    beezup_store_ids = fields.Char(
        string='Beezup store IDs',
        help='You can indicate one or more store ids separated by commas.'
    )
    beezup_username = fields.Char(
        string='Beezup username',
        help='Beezup login username',
    )
    beezup_token = fields.Char(
        string='Beezup user token',
    )
    beezup_last_sync = fields.Datetime(
        string='Beezup last sync done',
        default=fields.Datetime.now,
    )
    beezup_test_mode = fields.Boolean(
        string='Beezup test mode',
    )
    beezup_carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
        default=_default_carrier_id,
    )
    beezup_payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode',
        string='Payment mode',
        default=_default_payment_mode_id,
    )
    beezup_partner_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Partner account',
        default=_default_partner_account_id,
        domain=lambda self: self._get_beezup_partner_account_id_domain(),
        help='Partner\'s account receivable to be assigned to the invoice '
             'lines, if created.',
    )
    beezup_shipping_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Shipping product',
        default=_default_shipping_product_id,
    )
    beezup_journal_payment_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal payment',
        default=_default_journal_payment_id,
        domain=[('type', 'in', ['bank', 'cash'])],
        help='Payment journal to pay the invoice, if created.'
    )
    beezup_fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Spanish fiscal position',
        default=_default_fiscal_position_id,
        help='Tax position for calculating prices and taxes for country code '
             '\'ES\'.'
    )
    beezup_force_partner = fields.Boolean(
        string='Force partner',
        help='If you check this field, you must fill the "Parent company" '
             'field and each contact that is imported will be assigned that '
             'company as the parent. Also, in the generated sales order, this '
             'parent company will be assigned as the invoice address.',
    )
    beezup_parent_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Parent partner',
    )
    beezup_tax_ids = fields.Many2many(
        string='Product account taxs',
        comodel_name='account.tax',
        relation='company_beezup_tax_rel',
        column1='company_id',
        column2='tax_id',
        required=True,
        domain=[('type_tax_use', '=', 'sale')],
        help='Customer taxes that will be assigned by default when the system '
             'has to create a product automatically when importing an order '
             'from Beezup.'
    )
    sale_number_overwrite = fields.Boolean(
        string='Overwrite sale number',
        help='If you check this field, sale namber will be set with Beezup '
             'number instead of next sequence number.',
    )
    beezup_default_picking_policy = fields.Selection(
        string='Beezup picking policy',
        selection=[
            ('auto', 'Automatic'),
            ('manual', 'Manual'),
        ],
        help='If automatic is selected, Beezup stock pickings will be processed'
             ' automatically.',
        default='auto',
    )
