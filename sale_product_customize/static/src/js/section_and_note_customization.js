odoo.define('sale_product_customize.section_and_note_backend', function (require) {
    "use strict";
    var pyUtils = require('web.py_utils');
    var core = require('web.core');
    var _t = core._t;
    var fieldRegistry = require('web.field_registry');
    var SectionAndNoteFieldOne2Many = fieldRegistry.get('section_and_note_one2many')
    var CustomizationFieldOne2Many = SectionAndNoteFieldOne2Many.extend({
        _getRenderer: function () {
            var render = this._super();
            if (this.view.arch.tag !== 'tree') {
                return render;
            }
            var RenderExtended = render.extend({
                _getData: function () {
                    var saleOrderForm = this.getParent() && this.getParent().getParent();
                    var stateData = saleOrderForm && saleOrderForm.state && saleOrderForm.state.data;
                    console.log('stateData', stateData)
                    return stateData
                },
                _onAddRecord: function (ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    var self = this;
                    var context = ev.currentTarget.dataset.context;
                    if (!(context && pyUtils.py_eval(context).open_sale_customization_add)){
                        return this._super.apply(this, arguments);
                    }
                    self._getData()
                    this.unselectRow().then(function () {
                        self._rpc({
                            model: 'ir.model.data',
                            method: 'xmlid_to_res_id',
                            kwargs: {
                                xmlid: 'sale_product_customize.sale_customization_add_form'
                            },
                        }).then(function (res_id) {
                            self.do_action({
                                name: _t('Customize a product'),
                                type: 'ir.actions.act_window',
                                res_model: 'sale.customization.add',
                                views: [[res_id, 'form']],
                                target: 'new',
                                context: {
                                    default_sale_id: 1
                                }
                            }, {
                                on_close: function (info) {
                                    console.log('returned data?', info)
                                    if (info) {
                                        self.trigger_up('add_record', {
                                            context: info,
                                            forceEditable: "bottom" ,
                                            allowWarning: true,
                                            onSuccess: function (){
                                                self.unselectRow();
                                            }
                                        });
                                    }
                                }
                            });
                        });
                    });
                }
            });
            return RenderExtended;
        }
    });

    fieldRegistry.add('section_and_note_one2many', CustomizationFieldOne2Many);
});
