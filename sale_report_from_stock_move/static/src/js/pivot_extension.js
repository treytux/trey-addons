odoo.define('sale_report_from_stock_move.PivotController', function (require) {
    'use strict';
    var _t = require('web.core')._t;
    var PivotController = require('web.PivotController');
    var framework = require('web.framework');
    PivotController.include({
        _getMarginBaseMeasure: function (measures) {
            if (measures.indexOf('price_unit') !== -1) {
                return 'price_unit';
            }
            return false;
        },
        _getMarginOperationMeasure: function (measures) {
            if (measures.indexOf('operation_total') !== -1) {
                return 'operation_total';
            }
            return false;
        },
        _downloadTable: function () {
            if (this.modelName !== 'sale.report.from_stock_move') {
                return this._super.apply(this, arguments);
            }
            var table = this.model.exportData();
            table.title = this.title || _t('Sales Analysis');
            var state = this.model.get();
            var measures = state.measures || [];
            var baseMeasure = this._getMarginBaseMeasure(measures);
            var operationMeasure = this._getMarginOperationMeasure(measures);
            table.technical_measures = measures;
            if (!baseMeasure || !operationMeasure) {
                return this.getSession().get_file({
                    url: '/web/pivot/export_custom_xls',
                    data: { data: JSON.stringify(table) },
                    complete: framework.unblockUI,
                });
            }
            var numMeasures = measures.length;
            var idxBase = measures.indexOf(baseMeasure);
            var idxOperation = measures.indexOf(operationMeasure);
            var new_measure_row = [];
            table.measure_row.forEach(function (m, i) {
                new_measure_row.push(m);
                if ((i + 1) % numMeasures === 0) {
                    new_measure_row.push({ measure: _t('% Margin'), is_bold: true });
                }
            });
            table.measure_row = new_measure_row;
            if (table.headers) {
                table.headers.forEach(function (row) {
                    row.forEach(function (cell) {
                        if (cell.colspan) {
                            cell.colspan = Math.round((cell.colspan / numMeasures) * (numMeasures + 1));
                        }
                    });
                });
            }
            var getExcelLetter = function (colNum) {
                var letter = '';
                while (colNum > 0) {
                    var temp = (colNum - 1) % 26;
                    letter = String.fromCharCode(temp + 65) + letter;
                    colNum = (colNum - temp - 1) / 26;
                }
                return letter;
            };
            var headerRows = (table.headers ? table.headers.length : 0) + 1;
            table.rows.forEach(function (row, rowIndex) {
                var newValues = [];
                var excelRow = rowIndex + headerRows + 1;
                for (var v = 0; v < row.values.length; v += numMeasures) {
                    var groupIndex = Math.floor(v / numMeasures);
                    var baseColNum = 2 + (groupIndex * (numMeasures + 1)) + idxBase;
                    var operationColNum = 2 + (groupIndex * (numMeasures + 1))
                        + idxOperation;
                    var bLet = getExcelLetter(baseColNum);
                    var oLet = getExcelLetter(operationColNum);
                    for (var m = 0; m < numMeasures; m++) {
                        newValues.push(row.values[v + m]);
                    }
                    var formula = '=(1-('
                        + bLet + excelRow + '/' + oLet + excelRow
                        + '))*100';
                    newValues.push({
                        value: formula,
                        is_bold: true,
                    });
                }
                row.values = newValues;
            });
            return this.getSession().get_file({
                url: '/web/pivot/export_custom_xls',
                data: { data: JSON.stringify(table) },
                complete: framework.unblockUI,
            });
        },
    });
});
