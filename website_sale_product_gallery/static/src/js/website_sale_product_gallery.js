
openerp.website_sale_product_gallery = function(instance) {
    var _t = instance.web._t;

    instance.web.form.WidgetGalleryImage = instance.web.form.AbstractField.extend({
        template: 'WidgetGalleryImage',
        render_value: function() {
            this._super();
            this.$("img").attr("src", this.get_value());
            if (this.node.attrs.class) {
                this.$el.addClass(this.node.attrs.class);
            }
        }
    });

    instance.web.form.widgets = instance.web.form.widgets.extend({
        'image_gallery': 'instance.web.form.WidgetGalleryImage',
    });


    instance.web.list.WidgetGalleryImage = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            //console.debug("row options", row_data, options);
            var url = '';
            if (row_data.image) {
                url = 'data:image/png;base64,' + row_data.image.value;
            } else {
                url = '/images/50x50/' + row_data.name.value + '?r=' + new Date().getTime();
            }

            return _.str.sprintf('<img src="%s" readonly="readonly" height="50px"/>', url);
        }
    });

    instance.web.list.columns.add('field.image_gallery', 'instance.web.list.WidgetGalleryImage');
};
