###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'portal.mixin']

    signed_by = fields.Char(
        string='Signed by',
        help='Name of the person that signed the picking.',
        copy=False,
    )
    is_signed = fields.Boolean(
        string='Is signed',
    )
    pending_signed = fields.Selection(
        selection=[
            ('not_signed', 'Not signed'),
            ('pending', 'Pending'),
            ('signed', 'Signed'),
            ('cancel', 'Cancel'),
        ],
        string='Pending signed',
        default='not_signed',
    )

    def _compute_access_url(self):
        super(StockPicking, self)._compute_access_url()
        for picking in self:
            picking.access_url = '/my/pending_pickings/%s' % (picking.id)

    def get_pending_picking_sign_portal(self):
        picking = self.env['stock.picking'].browse(self.env.context['picking'])
        return picking.pending_signed

    def print_picking_report_sale_session(self):
        picking = self.env['stock.picking'].browse(self.env.context['picking'])
        commercial_partner_id = picking.partner_id.commercial_partner_id
        if commercial_partner_id.delivery_slip_type == 'valued':
            return self.env.ref(
                'print_formats_picking_valued.'
                'report_stock_deliveryslip_valued_create'
            ).report_action(picking)
        else:
            return self.env.ref(
                'stock.action_report_delivery').report_action(picking)

    def set_cancel_pending_picking(self):
        picking = self.env['stock.picking'].browse(self.env.context['picking'])
        picking.pending_signed = 'cancel'
        return True

    def call_signature_portal_from_picking(self, context):
        module_name = 'portal_stock_picking_signature'
        action_name = 'signature_picking_sale_session_action'
        action = self.env.ref('%s.%s' % (module_name, action_name))
        self.pending_signed = 'pending'
        context['picking'] = self.id
        vals = action.read()[0]
        vals['context'] = context
        return vals
