###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'portal.mixin']

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
        super()._compute_access_url()
        for picking in self:
            picking.access_url = '/my/pending_picking/%s' % (picking.id)

    def get_pending_picking_sign_portal(self):
        picking = self.env['stock.picking'].browse(self.env.context['picking'])
        return picking.pending_signed

    def print_picking_report_sale_session(self):
        picking = self.env['stock.picking'].browse(self.env.context['picking'])
        if hasattr(picking, 'do_print_picking_valued'):
            return picking.do_print_picking_valued()
        return self.env.ref('stock.action_report_delivery').report_action(
            picking, config=False)

    def set_cancel_pending_picking(self):
        picking = self.env['stock.picking'].browse(self.env.context['picking'])
        picking.pending_signed = 'cancel'
        return True

    def call_signature_portal_from_picking(self):
        module_name = 'portal_stock_picking_signature'
        action_name = 'signature_picking_sale_session_action'
        vals = self.env['ir.actions.actions']._for_xml_id(
            '%s.%s' % (module_name, action_name))
        self.pending_signed = 'pending'
        vals['context'] = dict(self.env.context, picking=self.id)
        return vals
