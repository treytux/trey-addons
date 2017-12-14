(function() {
    'use strict';
    var instance = openerp;
    openerp.widget_grid = function(instance)
    {
        instance.web.form.widgets.add(
            'widget_grid',
            'instance.widget_grid.widgetGrid');
        instance.widget_grid.widgetGrid = instance.web_widget_x2many_2d_matrix.FieldX2Many2dMatrix.extend({
            template: 'widgetGridTemplate',
            widget_class: 'oe_form_widget_grid',

            // Wizard_--> Widget configuration values
            field_x_axis: 'x',
            field_label_x_axis: 'x',
            field_y_axis: 'y',
            field_label_y_axis: 'y',
            field_value: 'value',
            field_available_label: '',
            available_block: 0,
            field_disabled: 0,

            fields_att: {},
            x_axis_clickable: true,
            y_axis_clickable: true,

            init: function(field_manager, node)
            {
                self = this;
                self.field_x_axis = node.attrs.field_x_axis || this.field_x_axis;
                self.available_block = node.attrs.available_block;
                self.field_disabled = node.attrs.field_disabled || this.field_disabled;
                self.field_y_axis = node.attrs.field_y_axis || this.field_y_axis;
                self.x_axis_clickable = node.attrs.x_axis_clickable || this.x_axis_clickable;
                self.y_axis_clickable = node.attrs.y_axis_clickable || this.y_axis_clickable;
                self.field_label_x_axis = node.attrs.field_label_x_axis || this.field_x_axis;
                self.field_label_y_axis = node.attrs.field_label_y_axis || this.field_y_axis;
                self.field_value = node.attrs.field_value || this.field_value;
                self.field_available_label = node.attrs.field_available_label;
                return this._super.apply(this, [field_manager, node]);
            },

            xy_value_change: function(e) {
                var $this = jQuery(e.currentTarget),
                    val = $this.val(),
                    qty_available = this.by_id[$this.data('id')]['qty_available'],
                    stock = $this.parent().parent().find('.wg_show_stock'),
                    no_stock_control = stock.val() === undefined;
                this._super(e);
                if (no_stock_control) {
                    if(! this.validate_xy_value(val) && parseInt(val) > 0){
                        $this.parent().addClass('oe_form_invalid');
                    }
                }else{
                    var invalid_input = ! this.validate_xy_value(val) && parseInt(val) > 0,
                        not_qty_available = val > qty_available || parseInt(val) <= 0,
                        again_cero = parseInt(val) === 0 && val == '0';
                    if(invalid_input){
                        $this.parent().addClass('oe_form_invalid');
                    } else if(this.validate_xy_value(val) && parseInt(val) > 0){
                        $this.parent().addClass('oe_form_invalid');
                    } else if(not_qty_available){
                        $this.parent().addClass('oe_form_invalid');
                        $this.parent().parent().find('.qty_available').attr('style', 'color: #c00;');
                    } if (again_cero){
                        $this.parent().parent().find('.qty_available').removeAttr('style');
                        $this.parent().removeClass('oe_form_invalid');
                    } else {
                        $this.parent().parent().find('.qty_available').removeAttr('style');
                    }
                }
            }
        });
    }
})();



