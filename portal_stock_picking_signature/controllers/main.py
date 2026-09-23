###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class CustomerPortal(CustomerPortal):
    @http.route(
        ['/my/picking_sign'], type='http', auth='user', website=True)
    def portal_my_picking_sign(self):
        sale = request.env['sale.order'].search([
            ('create_uid', '=', request.env.user.id),
            ('state', '=', 'sale'),
        ], order='create_date desc', limit=1)
        if not sale:
            values = {
                'page_name': 'picking_sign',
                'pending_picking': False,
            }
            return request.render(
                'portal_stock_picking_signature.portal_my_picking_sign',
                values)
        pending_picking = request.env['stock.picking'].search([
            ('sale_id', '=', sale.id),
            ('state', '=', 'done'),
            ('is_signed', '=', False),
            ('pending_signed', '=', 'pending'),
        ], order='create_date desc', limit=1).id
        values = {
            'page_name': 'picking_sign',
            'pending_picking': pending_picking,
        }
        return request.render(
            'portal_stock_picking_signature.portal_my_picking_sign',
            values)

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        values.update({
            'page_name': 'picking_sign',
        })
        return values

    @http.route(
        ['/my/pending_picking/<int:picking_id>'], type='http', auth='user',
        website=True)
    def portal_my_pending_picking(self, picking_id):
        pending_picking = request.env['stock.picking'].browse(picking_id)
        if not pending_picking:
            return
        values = {
            'page_name': 'picking_sign',
            'pending_picking': pending_picking,
        }
        return request.render(
            'portal_stock_picking_signature.portal_my_pending_picking',
            values)

    @http.route(
        ['/my/pending_picking/<int:picking_id>/accept'],
        type='json', auth='public', website=True)
    def portal_my_pending_picking_accept(
        self, res_id, access_token=None, partner_name=None, signature=None,
            picking_id=None):
        try:
            pending_picking_sudo = self._document_check_access(
                'stock.picking', res_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order')}
        if not signature:
            return {'error': _('Signature is missing.')}
        pending_picking_sudo.write({
            'signature': signature,
            'signed_by': partner_name,
            'is_signed': True,
            'pending_signed': 'signed',
            'signature_datetime': fields.Datetime.now(),
            'signature_filename': partner_name,
        })
        return {
            'force_refresh': True,
            'redirect_url': '/my/picking_sign',
        }

    @http.route(
        ['/my/pending_picking/<int:picking_id>/cancel'],
        type='http', auth='public', website=True)
    def portal_my_pending_picking_cancel(self, picking_id, access_token=None):
        try:
            picking = self._document_check_access(
                'stock.picking', picking_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order')}
        picking.write({
            'pending_signed': 'cancel',
        })
        return request.redirect('/my/picking_sign')
