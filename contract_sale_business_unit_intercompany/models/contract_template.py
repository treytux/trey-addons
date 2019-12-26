###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api


class ContractTemplate(models.Model):
    _inherit = 'contract.template'

    unit_id = fields.Many2one(
        comodel_name='product.business.unit',
        compute='_compute_unit_id',
        readonly=True,
        store=True,
        string='Business unit',
    )
    area_id = fields.Many2one(
        comodel_name='product.business.area',
        string='Area',
    )
    business_display_name = fields.Char(
        string='Business Display Name',
        compute='_compute_business_display_name',
    )

    @api.multi
    @api.depends('area_id')
    def _compute_unit_id(self):
        for contract in self:
            contract.unit_id = (
                contract.area_id.unit_id.id if contract.area_id else False)

    @api.multi
    @api.depends('unit_id', 'area_id')
    def _compute_business_display_name(self):
        display_name = self.env['product.template'].business_display_name_get
        for contract in self:
            contract.business_display_name = display_name(contract)

    @api.multi
    @api.constrains('unit_id', 'area_id')
    def _check_area_id(self):
        self.env['product.template'].check_area_id(self)
