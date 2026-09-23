###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging

import pandas as pd
from odoo import _, fields, models

_log = logging.getLogger('Contract line lot import')


class ContractLineLotImport(models.TransientModel):
    _name = 'contract.line.lot.import'
    _description = 'Wizard to import and update lots in contract lines'

    file = fields.Binary(
        string='File',
        help='File with the lots of the contract lines',
        required=True,
    )
    filename = fields.Char(
        string='Filename',
    )
    line_ids = fields.One2many(
        comodel_name='contract.line.lot.import.line',
        inverse_name='wizard_id',
        string='Wizard lines',
    )
    step = fields.Integer(
        string='Step',
    )

    def find_contract(self, row, index):
        if not row['Suscripción']:
            msg = _('Row %s: The contract %s is not established in the row') % (
                index, row['Suscripción'])
            self._error(msg)
            return False
        contracts = self.env['contract.contract'].search([
            '|',
            ('name', 'ilike', row['Suscripción']),
            ('code', 'ilike', row['Suscripción']),
            ('active', 'in', [True, False]),
        ])
        if not contracts:
            msg = _('Row %s: No contract found %s') % (
                index, row['Suscripción'])
            self._error(msg)
            return False
        if len(contracts) > 1:
            msg = _('Row %s: More than one contract %s has been found') % (
                index, row['Suscripción'])
            self._error(msg)
            return False
        return contracts[0]

    def find_contract_product_line(self, row, index):
        if not row['Modalidad Mantenimiento']:
            msg = _('Row %s: The contract line product %s is not assigned') % (
                index, row['Modalidad Mantenimiento'])
            self._error(msg)
            return False
        products = self.env['product.product'].search([
            ('default_code', '=', row['Modalidad Mantenimiento']),
        ])
        if not products:
            msg = _('Row %s: No product %s found') % (
                index, row['Modalidad Mantenimiento'])
            self._error(msg)
            return False
        if len(products) > 1:
            msg = _('Row %s: More than one product %s has been found') % (
                index, row['Modalidad Mantenimiento'])
            self._error(msg)
            return False
        return products[0]

    def get_contract_line(self, contract, product, index):
        lines = contract.contract_line_ids.filtered(
            lambda ln: ln.product_id == product)
        if not lines:
            msg = _('Row %s: No contract line found with this product %s') % (
                index, product.default_code)
            self._error(msg)
            return False
        return lines[0]

    def get_product_lot_domain(self, row):
        return [('default_code', '=', row['P/N'])]

    def set_lot_contract_line(self, row, line, index, simulation=False):
        if row['S/N']:
            lots = self.env['stock.lot'].search([
                ('name', '=', row['S/N']),
            ])
            if not lots:
                if not row['P/N']:
                    msg = _('Row %s: The lot cannot be created because the'
                            ' product is not defined in the row') % index
                    self._error(msg)
                    return False
                products = self.env['product.product'].search(
                    self.get_product_lot_domain(row))
                if len(products) == 1:
                    if simulation:
                        msg = _('New lot created %s') % str(row['S/N']).strip()
                        self._warning(msg)
                        return False
                    lot = self.env['stock.lot'].create({
                        'name': row['S/N'],
                        'product_id': products[0].id,
                    })
                    return lot
                if len(products) > 1:
                    msg = _('Row %s: More than one product %s '
                            'has been found') % (index, row['P/N'])
                    self._error(msg)
                    return False
                if not products:
                    if not row['P/N']:
                        msg = _('Row %s: The lot cannot be created because the'
                                ' product is not defined in the row') % index
                        self._error(msg)
                        return False
                    if simulation:
                        msg = _('New product created %s') % str(
                            row['P/N']).strip()
                        self._warning(msg)
                        msg = _('New lot created %s') % str(row['S/N']).strip()
                        self._warning(msg)
                        return False
                    template = self.env['product.template'].create({
                        'name': str(row['P/N']).strip(),
                        'default_code': str(row['P/N']).strip(),
                        'type': 'product',
                        'tracking': 'lot',
                    })
                    product = template.product_variant_id
                    lot = self.env['stock.lot'].create({
                        'name': str(row['S/N']).strip(),
                        'product_id': product.id,
                    })
                    return lot
            if len(lots) > 1:
                msg = _('Row %s: More than one lot %s has been found') % (
                    index, row['S/N'])
                self._error(msg)
                return False
            lot = lots[0]
            if lot.id not in line.lot_ids.ids:
                return lot
            else:
                return False
        elif row['P/N']:
            products = self.env['product.product'].search(
                self.get_product_lot_domain(row))
            if not products:
                msg = _('Row %s: The lot cannot be assigned because the S/N '
                        'column is not set') % index
                self._error(msg)
                return False
            if len(products) > 1:
                msg = _('Row %s: More than one product %s has been found') % (
                    index, row['P/N'])
                self._error(msg)
                return False
            product = products[0]
            lots = self.env['stock.lot'].search([
                ('product_id', '=', product.id),
            ])
            if len(lots) == 1:
                if lots[0].id not in line.lot_ids.ids:
                    return lots[0]
                else:
                    return False
            else:
                msg = _('Row %s: The lot cannot be assigned because the '
                        'S/N column is not set') % index
                self._error(msg)
                return False
        else:
            msg = _('Row %s: The product and the lot are not established') % (
                index)
            self._error(msg)
            return False

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def _error(self, message):
        self.ensure_one()
        self.line_ids.create({
            'wizard_id': self.id,
            'name': message,
        })

    def _warning(self, message):
        self.ensure_one()
        self.line_ids.create({
            'wizard_id': self.id,
            'name': message,
            'type': 'warning',
        })

    def action_back(self):
        self.step = 0
        return self._reopen_view()

    def action_simulate(self):
        self.ensure_one()
        self.line_ids.unlink()
        file = io.BytesIO(base64.b64decode(self.file))
        df = pd.read_excel(file)
        df = df.fillna('')
        for _index, row in df.iterrows():
            _log.info('[%s/%s] %s' % (_index + 1, len(df), row['S/N']))
            contract = self.find_contract(row, _index + 1)
            if not contract:
                continue
            product = self.find_contract_product_line(row, _index + 1)
            if not product:
                continue
            line = self.get_contract_line(contract, product, _index + 1)
            if not line:
                continue
            lot = self.set_lot_contract_line(
                row, line, _index + 1, simulation=True)
            if not lot:
                continue
        self.step = 1
        return self._reopen_view()

    def button_accept(self):
        self.ensure_one()
        file = io.BytesIO(base64.b64decode(self.file))
        df = pd.read_excel(file)
        df = df.fillna('')
        for _index, row in df.iterrows():
            _log.info('[%s/%s] %s' % (_index + 1, len(df), row['S/N']))
            contract = self.find_contract(row, _index + 1)
            if not contract:
                continue
            product = self.find_contract_product_line(row, _index + 1)
            if not product:
                continue
            line = self.get_contract_line(contract, product, _index + 1)
            if not line:
                continue
            lot = self.set_lot_contract_line(row, line, _index + 1)
            if not lot:
                continue
            lines = self.env['contract.line'].search([
                ('lot_ids', 'in', lot.id),
            ])
            for contract_line in lines:
                contract_line.write({
                    'lot_ids': [(3, lot.id, 0)]
                })
            line.write({
                'lot_ids': [(4, lot.id)]
            })


class ContractLineLotImportLine(models.TransientModel):
    _name = 'contract.line.lot.import.line'
    _description = 'Contract line lot import lines'

    wizard_id = fields.Many2one(
        comodel_name='contract.line.lot.import',
        string='Wizard',
    )
    type = fields.Selection(
        selection=[
            ('error', 'Error'),
            ('warning', 'Warning'),
        ],
        string='Type',
        default='error',
    )
    name = fields.Char(
        string='Error message',
        required=True,
    )
