###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api, exceptions, _


class SaleCustomization(models.Model):
    _name = 'sale.customization'
    _description = 'Sale customization'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True)
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.user.company_id.id)
    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        required=True)
    state = fields.Selection(
        selection=[
            ('cancel', 'Canceled'),
            ('draft', 'Draft'),
            ('pending_logo', 'Pending logotype'),
            ('in_design', 'In design'),
            ('make_tests', 'Make tests'),
            ('sended_customer', 'Test sent to the customer'),
            ('validated', 'Validated by the customer')],
        string='State',
        default='draft')
    line_ids = fields.One2many(
        comodel_name='sale.customization.line',
        inverse_name='customization_id',
        string='Lines')
    sale_line_ids = fields.One2many(
        string='Sale lines',
        comodel_name='sale.order.line',
        inverse_name='customization_id')
    sale_line_count = fields.Integer(
        string='Lines count',
        compute='_compute_sale_line_count')

    @api.multi
    @api.depends('sale_line_ids')
    def _compute_sale_line_count(self):
        for customization in self:
            customization.sale_line_count = len(self.sale_line_ids)

    @api.multi
    def action_pending_logo(self):
        if not self.line_ids:
            raise exceptions.Warning(_(
                'You must add fill in at least one line to customization!'))
        self.state = 'pending_logo'

    @api.multi
    def action_in_design(self):
        if not self.line_ids:
            raise exceptions.Warning(_(
                'You must add fill in at least one line to customization!'))
        for line in self.line_ids:
            if not line.image:
                # @TODO Posteriormente abriremos un asistente para adjuntar
                # los ficheros pdfs con los disenos en lugar del raise
                raise exceptions.Warning(_(
                    'You must fill in the logo\'s images before continuing!'))
        self.state = 'in_design'

    @api.multi
    def action_make_tests(self):
        self.state = 'make_tests'
        return {
            'name': _('Sale customization add file'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [],
            'res_model': 'sale.customization.add.file',
            'target': 'new',
            'type': 'ir.actions.act_window'}

    @api.multi
    def action_sended_customer(self):
        self.state = 'sended_customer'

    @api.multi
    def action_validated(self):
        self.state = 'validated'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

    @api.multi
    def action_revert_to_draft(self):
        self.state = 'draft'
