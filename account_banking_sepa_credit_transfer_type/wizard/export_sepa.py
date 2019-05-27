# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api
from lxml import etree


class BankingExportSepaWizard(models.TransientModel):
    _inherit = ['banking.export.sepa.wizard']

    category_purpose = fields.Selection(
        string='Category Purpose',
        selection=[('DIVI', 'Payment of Dividends'),
                   ('INTC', 'Intra-company Payment'),
                   ('INTE', 'Payment of Interest'),
                   ('PENS', 'Payment of Pension'),
                   ('SALA', 'Payment of Salaries'),
                   ('SSBE', 'Payment of Child Benefit/Family Allowance'),
                   ('SUPP', 'Payment to a Supplier'),
                   ('TAXS', 'Payment of Taxes'),
                   ('TREA', 'Treasury Transaction')],
        required=False)

    @api.model
    def generate_start_payment_info_block(
            self, parent_node, payment_info_ident, priority,
            local_instrument, sequence_type, requested_date,
            eval_ctx, gen_args):
        res = super(
            BankingExportSepaWizard, self).generate_start_payment_info_block(
            parent_node=parent_node, payment_info_ident=payment_info_ident,
            priority=priority, local_instrument=local_instrument,
            sequence_type=sequence_type, requested_date=requested_date,
            eval_ctx=eval_ctx, gen_args=gen_args)
        if self.category_purpose:
            payment_type_info_2_6 = (res[0].findall('PmtTpInf'))[0]
            category_propose_2_15 = etree.SubElement(
                payment_type_info_2_6, 'CtgyPurp')
            category_propose_code_2_15 = etree.SubElement(
                category_propose_2_15, 'Cd')
            category_propose_code_2_15.text = self.category_purpose
        return res
