###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api, _
from odoo.exceptions import UserError
from lxml import etree


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.model
    def generate_creditor_scheme_identification(
        self, parent_node, identification, identification_label,
            eval_ctx, scheme_name_proprietary, gen_args):
        if '.payment_mode_id.sepa_creditor_identifier or' in identification:
            identification = (
                'self.journal_id.sepa_creditor_identifier or '
                'self.payment_mode_id.sepa_creditor_identifier or '
                'self.company_id.sepa_creditor_identifier')
        return super().generate_creditor_scheme_identification(
            parent_node, identification, identification_label, eval_ctx,
            scheme_name_proprietary, gen_args)

    @api.model
    def generate_initiating_party_block(self, parent_node, gen_args):
        my_company_name = self._prepare_field(
            'Company Name',
            'self.company_partner_bank_id.partner_id.name',
            {'self': self}, gen_args.get('name_maxsize'), gen_args=gen_args)
        initiating_party = etree.SubElement(parent_node, 'InitgPty')
        initiating_party_name = etree.SubElement(initiating_party, 'Nm')
        initiating_party_name.text = my_company_name
        initiating_party_identifier = (
            self.journal_id.initiating_party_identifier or
            self.payment_mode_id.initiating_party_identifier or
            self.payment_mode_id.company_id.initiating_party_identifier)
        initiating_party_issuer = (
            self.journal_id.initiating_party_issuer or
            self.payment_mode_id.initiating_party_issuer or
            self.payment_mode_id.company_id.initiating_party_issuer)
        initiating_party_scheme = (
            self.journal_id.initiating_party_scheme or
            self.payment_mode_id.initiating_party_scheme or
            self.payment_mode_id.company_id.initiating_party_scheme)
        # in pain.008.001.02.ch.01.xsd files they use
        # initiating_party_identifier but not initiating_party_issuer
        if initiating_party_identifier:
            iniparty_id = etree.SubElement(initiating_party, 'Id')
            iniparty_org_id = etree.SubElement(iniparty_id, 'OrgId')
            iniparty_org_other = etree.SubElement(iniparty_org_id, 'Othr')
            iniparty_org_other_id = etree.SubElement(iniparty_org_other, 'Id')
            iniparty_org_other_id.text = initiating_party_identifier
            if initiating_party_scheme:
                iniparty_org_other_scheme = etree.SubElement(
                    iniparty_org_other, 'SchmeNm')
                iniparty_org_other_scheme_name = etree.SubElement(
                    iniparty_org_other_scheme, 'Prtry')
                iniparty_org_other_scheme_name.text = initiating_party_scheme
            if initiating_party_issuer:
                iniparty_org_other_issuer = etree.SubElement(
                    iniparty_org_other, 'Issr')
                iniparty_org_other_issuer.text = initiating_party_issuer
        elif self._must_have_initiating_party(gen_args):
            raise UserError(
                _("Missing 'Initiating Party Issuer' and/or "
                    "'Initiating Party Identifier' for the company '%s'. "
                    "Both fields must have a value.")
                % self.company_id.name)
        return True
