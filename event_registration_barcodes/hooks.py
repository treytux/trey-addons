###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import SUPERUSER_ID, api

_log = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _log.info('Create barcodes for registrations without barcodes')
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        registrations = env['event.registration'].search([
            ('barcode', '=', False),
        ])
        for ticket in registrations:
            ticket.barcode = ticket.get_registration_barcode()
