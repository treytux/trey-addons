##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import api, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    def recompute_crm_team_locations(self):
        self.ensure_one()
        wh = self.warehouse_id
        teams = self.env['crm.team'].search([])
        teams.sudo().write({'location_ids': [(3, self.id)]})
        teams = self.env['crm.team'].search([('warehouse_ids', 'in', wh.ids)])
        teams.sudo().write({'location_ids': [(4, self.id)]})

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for location in res:
            location.recompute_crm_team_locations()
        return res

    def write(self, vals):
        res = super().write(vals)
        for location in self:
            location.recompute_crm_team_locations()
        return res
