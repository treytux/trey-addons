###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
import re

from odoo import _, fields, models


class ContractLiteLineServerOccupationImportWizard(models.TransientModel):
    _name = 'contract.lite.line.server.occupation.import.wizard'
    _description = 'Wizard to import server occupation for contract lines'

    customer_occupation = fields.Text(
        string='Customer Occupation',
        required=True,
    )
    result_summary = fields.Text(
        string='Result summary',
        readonly=True,
    )
    import_payload = fields.Text(
        string='Import payload',
        readonly=True,
    )

    def _parse_occupation(self):
        self.ensure_one()
        result = {}
        ignored_lines = []
        status_pattern = re.compile(
            r'^\[\s*(ERROR|OK)\s*\]',
            re.IGNORECASE,
        )
        occupation_pattern = re.compile(
            r'^\[\s*(ERROR|OK)\s*\]\s+([^:]+):\s+'
            r'([0-9]+(?:[\.,][0-9]+)?)G\b',
            re.IGNORECASE,
        )
        for raw_line in (self.customer_occupation or '').splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if not status_pattern.match(line):
                continue
            match = occupation_pattern.match(line)
            if not match:
                ignored_lines.append(line)
                continue
            container = match.group(2).strip()
            consumed = float(match.group(3).replace(',', '.'))
            result[container] = consumed
        return result, ignored_lines

    def _get_selected_contract_ids(self):
        active_model = self.env.context.get('active_model')
        if active_model != 'contract_lite.contract':
            return []
        return self.env.context.get('active_ids', [])

    def _find_server_lines(self, container, contract_ids):
        if not contract_ids:
            return self.env['contract_lite.line']
        return self.env['contract_lite.line'].search([
            ('contract_id', 'in', contract_ids),
            ('contract_id.active', '=', True),
            ('contract_id.state', '=', 'active'),
            ('is_product_server', '=', True),
            ('container_name', '=', container),
        ])

    def _format_summary(
        self,
        updated,
        updated_containers,
        not_found,
        ignored_lines,
    ):
        lines = [
            _('Updated lines: %s') % updated,
            _('Containers not found: %s') % len(not_found),
            _('Ignored error lines: %s') % len(ignored_lines),
        ]
        if updated_containers:
            lines.append('')
            lines.append(_('To update containers:'))
            for container, consumed, line_count in updated_containers:
                lines.append(
                    '- %s: %s GB (%s lines)'
                    % (container, consumed, line_count))
        if not_found:
            lines.append('')
            lines.append(_('Not found containers:'))
            lines.extend('- %s' % container for container in not_found)
        if ignored_lines:
            lines.append('')
            lines.append(_('Ignored lines:'))
            lines.extend('- %s' % line for line in ignored_lines)
        return '\n'.join(lines)

    def button_apply(self):
        self.ensure_one()
        occupations, ignored_lines = self._parse_occupation()
        contract_ids = self._get_selected_contract_ids()
        matched = 0
        updated_containers = []
        not_found = []
        updates = []
        for container, consumed in occupations.items():
            lines = self._find_server_lines(container, contract_ids)
            if not lines:
                not_found.append(container)
                continue
            updates.append({
                'container': container,
                'consumed': consumed,
                'line_ids': lines.ids,
            })
            matched += len(lines)
            updated_containers.append((container, consumed, len(lines)))
        self.result_summary = self._format_summary(
            matched, updated_containers, not_found, ignored_lines
        )
        self.import_payload = json.dumps(updates)
        return {
            'name': _('Import Customer Occupation'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def button_apply_changes(self):
        self.ensure_one()
        updates = json.loads(self.import_payload or '[]')
        for update in updates:
            self.env['contract_lite.line'].browse(update['line_ids']).write({
                'consumed_space_gb': update['consumed'],
            })
        return {'type': 'ir.actions.act_window_close'}
