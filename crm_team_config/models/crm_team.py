##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        relation='crm_team2warehouse_rel',
        column1='crm_team_id',
        column2='warehouse_id',
        string='Warehouses',
    )
    location_ids = fields.Many2many(
        comodel_name='stock.location',
        compute='_compute_locations',
        relation='crm_team2location_rel',
        column1='crm_team_id',
        column2='location_id',
        string='Locations',
    )
    payment_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='crm_team2payment_journal_rel',
        column1='crm_team_id',
        column2='payment_journal_id',
        domain=[('type', 'in', ('bank', 'cash'))],
        string='Payment journals',
    )
    invoice_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='crm_team2invoice_journal_rel',
        column1='crm_team_id',
        column2='invoice_journal_id',
        string='Invoice journals',
    )

    @api.multi
    @api.depends('warehouse_ids')
    def _compute_locations(self):
        location_obj = self.env['stock.location']
        all_locations = location_obj.search([])
        for crm_team in self:
            allow_location_ids = []
            for loc in all_locations:
                wh = loc.get_warehouse()
                if wh and wh in crm_team.warehouse_ids:
                    allow_location_ids.append(loc.id)
            if allow_location_ids:
                common_location_ids = location_obj.search([
                    ('usage', '!=', 'internal')]).ids
                allow_location_ids = list(
                    set(allow_location_ids + common_location_ids))
                crm_team.location_ids = [(6, 0, allow_location_ids)]
