###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class EventEvent(models.Model):
    _inherit = 'event.event'

    address_id = fields.Many2one(
        string='Main location',
    )
    address_ids = fields.Many2many(
        string='Extra locations',
        comodel_name='res.partner',
        relation='partner2event_rel',
        column1='event_id',
        column2='partner_id',
    )
    addresses = fields.Char(
        string='Locations',
        compute='_compute_addresses',
        store=True,
    )

    @api.depends('address_id', 'address_ids')
    def _compute_addresses(self):
        for event in self:
            event.addresses = ', '.join(
                event.address_id.mapped('name')
                + event.address_ids.mapped('name'))

    def write(self, vals):
        res = super().write(vals=vals)
        if not any(vals.get(val) for val in ['address_id', 'address_ids']):
            return res
        for event in self:
            if not event.product_ids:
                continue
            for event_product in event.product_ids:
                if (event_product.address_id.id
                        not in event.address_id.ids + event.address_ids.ids):
                    raise exceptions.ValidationError(_(
                        '\'%s\' location of product \'%s\' not in event '
                        'addresses.'
                    ) % (event_product.address_id.name, event_product.name))
        return res
