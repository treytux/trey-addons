###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class EventRegistrationBarcodes(models.TransientModel):
    _name = 'event.registration.barcodes'
    _description = 'Wizard to scan tickets with barcodes'

    _barcode_scanned = fields.Char(
        string='Barcode scanned',
        help='Last barcode scanned',
        store=False,
    )
    barcode = fields.Char(
        string='Barcode',
    )
    event_id = fields.Many2one(
        comodel_name='event.event',
        string='Event',
    )
    line_ids = fields.Many2many(
        comodel_name='event.barcodes.line',
        compute='_compute_line_ids',
        string='Validated tickets',
    )
    message_type = fields.Selection(
        selection=[
            ('success', 'Ticket successfully validated'),
            ('done', 'Ticket has already been validated'),
            ('other_event', 'Ticket does not belong to this event'),
            ('cancel', 'Ticket is canceled'),
            ('error', 'Ticket not found'),
            ('not_confirmed', 'Ticket not confirmed'),
        ],
        readonly=True,
    )
    message = fields.Char(
        string='Message',
        readonly=True,
    )

    @api.depends('barcode')
    def _compute_line_ids(self):
        lines = self.env['event.barcodes.line'].search([
            ('wizard_id', '=', self.env.context['wizard_id']),
        ])
        self.line_ids = lines

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        lines = self.env['event.barcodes.line'].search([])
        lines.unlink()
        return res

    @api.onchange('_barcode_scanned')
    def _on_barcode_scanned(self):
        barcode = self._barcode_scanned
        if barcode:
            self._barcode_scanned = ''
            return self.on_barcode_scanned(barcode)

    def on_barcode_scanned(self, barcode):
        self.barcode = barcode
        self.read_event_ticket(barcode)
        return

    def _set_message_info(self, message_type, message):
        self.message_type = message_type
        if self.barcode:
            self.message = _('Barcode: %s (%s)') % (self.barcode, message)
        else:
            self.message = '%s' % message

    def read_event_ticket(self, barcode):
        wizard_lines_obj = self.env['event.barcodes.line']
        ticket = self.env['event.registration'].search([
            ('barcode', '=', barcode),
            ('event_id', '=', self.event_id.id),
        ])
        if len(ticket) == 0:
            ticket = self.env['event.registration'].search([
                ('barcode', '=', barcode),
            ])
            if len(ticket) == 1:
                self._set_message_info(
                    'other_event', _('Ticket does not belong to this event'))
            elif len(ticket) == 0:
                self._set_message_info('error', _('Ticket not found'))
            return
        if ticket.state == 'draft':
            self._set_message_info('not_confirmed', _('Ticket not confirmed'))
            return
        if ticket.state == 'done':
            self._set_message_info(
                'done', _('Ticket has already been validated'))
            return
        if ticket.state == 'cancel':
            self._set_message_info('cancel', _('Ticket is canceled'))
            return
        ticket.button_reg_close()
        self._set_message_info('success', _('Ticket successfully validated'))
        wizard_lines_obj.create({
            'wizard_id': self._origin.id,
            'name': ticket.name,
            'barcode': barcode,
        })
        return


class EventBarcodesLine(models.TransientModel):
    _name = 'event.barcodes.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='event.registration.barcodes',
        string='Wizard',
    )
    name = fields.Char(
        string='Ticket name',
    )
    barcode = fields.Char(
        string='Barcode',
    )
