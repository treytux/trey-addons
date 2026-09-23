###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools import str2bool


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
            ('pending_signed', '=', 'pending'),
        ], order='create_date desc', limit=1).id
        values = {
            'page_name': 'picking_sign',
            'pending_picking': pending_picking,
        }
        return request.render(
            'portal_stock_picking_signature.portal_my_picking_sign', values)

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
            'portal_stock_picking_signature.portal_my_pending_picking', values)

    @http.route(
        ['/my/pending_picking/<int:picking_id>/accept'],
        type='json', auth='public', website=True)
    def portal_my_pending_picking_accept(
            self, picking_id, access_token=None, name=None, signature=None):
        try:
            pending_picking_sudo = self._document_check_access(
                'stock.picking', picking_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order')}
        if not signature:
            return {'error': _('Signature is missing.')}
        pending_picking_sudo.write({
            'signature': signature,
            'signed_by': name,
            'pending_signed': 'signed',
            'signature_datetime': fields.Datetime.now(),
            'signature_filename': name,
        })
        return {
            'force_refresh': True,
            'redirect_url': '/my/picking_sign',
        }

    @http.route(
        ['/my/pending_picking/<int:picking_id>/accept_photo'],
        type='json', auth='public', website=True)
    def portal_my_pending_picking_accept_photo(
            self, picking_id, access_token=None, name=None, image=None,
            filename=None):
        try:
            pending_picking_sudo = self._document_check_access(
                'stock.picking', picking_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order')}
        if not image:
            return {'error': _('Photo is missing.')}
        image_b64 = image.split(',', 1)[-1]
        pending_picking_sudo.sudo().store_delivery_proof_photo(
            image_b64, filename)
        pending_picking_sudo.write({
            'signed_by': name,
            'pending_signed': 'signed',
            'signature_datetime': fields.Datetime.now(),
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

    @http.route(
        ['/picking/<int:picking_id>/delivery_proof'],
        type='http', auth='user', website=False)
    def picking_delivery_proof(self, picking_id, download=False, **kw):
        picking = request.env['stock.picking'].browse(picking_id).exists()
        if not picking:
            raise request.not_found()
        picking.check_access_rights('read')
        picking.check_access_rule('read')
        if not picking.delivery_proof_attachment_id:
            raise request.not_found()
        stream = request.env['ir.binary']._get_stream_from(
            picking.delivery_proof_attachment_id.sudo(), 'raw')
        return stream.get_response(
            as_attachment=str2bool(download, False))
