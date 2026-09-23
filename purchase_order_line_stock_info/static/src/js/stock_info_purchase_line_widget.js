odoo.define('purchase_order_line_stock_info.StockInfoPurchaseLineWidget', function (require) {
    'use strict';

    var core = require('web.core');
    var ListRenderer = require('web.ListRenderer')
    var QWeb = core.qweb;
    var Widget = require('web.Widget');
    var widget_registry = require('web.widget_registry');
    var _t = core._t;
    var time = require('web.time');

    ListRenderer.include({
        /**
         * @override
         */
        _renderBodyCell: function (record, node) {
            var $td = this._super.apply(this, arguments);
            if (node.tag === 'widget' && node.attrs.name === 'stock_info_purchase_line_widget') {
                $td.addClass('o_list_button');
            }
            return $td;
        }
    })
    var StockInfoPurchaseLineWidget = Widget.extend({
        template: 'purchase_order_line_stock_info.StockInfoPurchaseLineWidget',
        events: _.extend({}, Widget.prototype.events, {
            'click .fa-info-circle': '_onClickButton',
        }),
    /**
     * @override
     * @param {Widget|null} parent
     * @param {Object} params
     */
    init: function (parent, params){
        this.data = params.data;
        this._super(parent);
    },
    start: function (){
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self._setPopOver();
        });
    },
    updateState: function (state) {
        this.$el.popover('dispose');
        var candidate = state.data[this.getParent().currentRow];
        if (candidate) {
            this.data = candidate.data;
            this.renderElement();
            this._setPopOver();
        }
    },
    _setPopOver: function () {
        var self = this;
        var $content = $(QWeb.render('purchase_order_line_stock_info.StockInfoPurchaseLineDetails', {
            data: this.data,
        }));
        var options = {
            content: $content,
            html: true,
            placement: 'left',
            title: _t('Stock'),
            trigger: 'focus',
            delay: {'show': 0, 'hide': 100 },
        };
        this.$el.popover(options);
    },
    _onClickButton: function (){
        this.$el.find('.fa-info-circle').prop('special_click', true);
    },
});
    widget_registry.add('stock_info_purchase_line_widget', StockInfoPurchaseLineWidget);
    return StockInfoPurchaseLineWidget;
});
