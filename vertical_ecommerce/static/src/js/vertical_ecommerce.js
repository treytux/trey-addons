odoo.define('vertical_ecommerce.ProductsLayout', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let ProductsLayout = Class.extend({
        grid_selector: '#products_grid_before',
        categories_selector: '#products_grid_before > .nav.nav-pills',
        init: function () {
            let self = this
            let $grid = $(self.grid_selector)
            let $categories = $(self.categories_selector)
            if($grid.length > 0 && $categories.length > 0) {
                self.move_categories()
            }
        },
        move_categories: function () {
            let self = this
            $(self.categories_selector).detach().prependTo(self.grid_selector)
        },
    })
    let products_layout = new ProductsLayout()
    return {
        ProductsLayout: ProductsLayout,
        products_layout: products_layout,
    }
})
