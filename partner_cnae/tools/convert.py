# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import csv


class Csv:
    doc = None
    lines = []
    pos = -1
    cols = [chr(i) for i in range(ord('a'), ord('z') + 1)]

    def __init__(self, ffile, delimiter=',', quotechar='"'):
        self.doc = csv.reader(ffile, delimiter=delimiter, quotechar=quotechar)
        self.lines = [r for r in self.doc]
        self.pos = -1

    def get(self, col, formatter='str'):
        col_index = self.cols.index(col.lower())
        line = self.lines[self.pos]
        value = line[col_index]
        if hasattr(self, '_get_%s' % formatter):
            fnc = getattr(self, '_get_%s' % formatter)
        else:
            fnc = getattr(self, '_get_str')

        return fnc(value)

    def _get_str(self, value):
        return value

    def _get_int(self, value):
        try:
            return int(value)
        except:
            return int(0)

    def _get_float(self, value):
        try:
            return float(value)
        except:
            return float(0.0)

    def next(self, start=0, limit=None):
        if limit and limit - 2 < self.pos:
            return False

        if self.pos < 0:
            self.pos = start
            return True

        if self.pos + 1 < len(self.lines):
            self.pos += 1
            return True

        return False


cnae_ref = {}
doc = Csv(open('./CNAE.csv', 'r'), delimiter=';')
with file('../data/cnae_data.xml', 'w') as fp:
    fp.write('<?xml version="1.0" encoding="utf-8"?>\n')
    fp.write('<openerp>\n')
    fp.write('<data noupdate="0">\n')

    while doc.next(start=1):
        cnae_ref[doc.get('a')] = doc.get('c')
        fp.write('\n')
        fp.write('    <record id="cnae_%s" model="partner_cnae.cnae">\n' %
                 doc.get('c'))
        fp.write('        <field name="code">%s</field>\n' %
                 doc.get('c'))
        if doc.get('b', 'int'):
            fp.write('        <field name="parent_id" ref="cnae_%s"/>\n' %
                     cnae_ref[doc.get('b')])
        fp.write('        <field name="name">%s</field>\n' %
                 doc.get('d'))
        fp.write('    </record>\n')

    fp.write('</data>\n')
    fp.write('</openerp>\n')

doc = Csv(open('./CNAE_risk.csv', 'r'), delimiter=';')
with file('../data/cnae_risk_data.xml', 'w') as fp:
    fp.write('<?xml version="1.0" encoding="utf-8"?>\n')
    fp.write('<openerp>\n')
    fp.write('<data noupdate="0">\n')

    while doc.next(start=1):
        if doc.get('b') != '2013':
            continue

        fp.write('\n')
        fp.write(
            '    <record id="risk_%s_%s" model="partner_cnae.cnae_risk">\n' % (
                doc.get('a'), doc.get('b', 'int')))
        fp.write('        <field name="cnae_id" ref="cnae_%s"/>\n' % doc.get(
            'a'))
        fp.write('        <field name="year">%s</field>\n' % doc.get(
            'b', 'int'))
        fp.write('        <field name="coef_it">%s</field>\n' % doc.get(
            'c', 'float'))
        fp.write('        <field name="coef_ims">%s</field>\n' % doc.get(
            'd', 'float'))
        fp.write('        <field name="coef_total">%s</field>\n' % doc.get(
            'e', 'float'))
        fp.write('    </record>\n')

    fp.write('</data>\n')
    fp.write('</openerp>\n')
