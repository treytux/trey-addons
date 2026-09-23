###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectTaskLineExtra(models.Model):
    _name = 'project.task.line.extra'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Project task line extra'

    name = fields.Char(
        string='Name',
        translate=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company.id,
    )
    project_task_id = fields.Many2one(
        comodel_name='project.task',
        string='Project task',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        default=1,
    )
    price_unit = fields.Float(
        string='Price unit',
        digits='Product Price',
    )
    date_to_invoice = fields.Date(
        string='Date to invoice',
        default=fields.Date.today(),
        help='Date on which this line will be invoiced.',
    )
    invoice_line_ids = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='project_task_line_extra_id',
        string='Invoice line',
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='project_task_line_extra_partner_id_rel',
        column1='line_extra_id',
        column2='partner_id',
        required=True,
        string='Participants',
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        self.name = self.product_id.display_name
        project = self.project_task_id.project_id
        fiscal_position = (
            project
            and project.partner_id
            and project.partner_id.property_account_position_id or None)
        self.price_unit = self.product_id._get_tax_included_unit_price(
            self.company_id,
            project.currency_id or self.company_id.currency_id,
            None,
            'sale',
            fiscal_position=fiscal_position,
            product_uom=self.product_id.uom_id,
        )
        self.partner_ids = [(6, 0, self.project_task_id.partner_ids.ids)]

    def _prepare_invoice_line(self):
        self.ensure_one()
        return {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': self.quantity,
            'price_unit': self.price_unit,
            'project_task_line_extra_id': self.id,
        }
