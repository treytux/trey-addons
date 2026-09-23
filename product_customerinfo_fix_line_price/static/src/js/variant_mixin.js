odoo.define('product_customerinfo_fix_line_price.VariantMixin', function (require) {
'use strict';

var ajax = require('web.ajax');
var core = require('web.core');
var session = require('web.session');
var VariantMixin = require('sale.VariantMixin');

VariantMixin._getCombinationInfo = function (ev) {
    if ($(ev.target).hasClass('variant_custom_value')) {
        return Promise.resolve();
    }

    const $parent = $(ev.target).closest('.js_product');
    if(!$parent.length){
        return Promise.resolve();
    }
    const combination = this.getSelectedVariantValues($parent);
    let parentCombination;

    if ($parent.hasClass('main_product')) {
        parentCombination = $parent.find('ul[data-attribute_exclusions]').data('attribute_exclusions').parent_combination;
        const $optProducts = $parent.parent().find(`[data-parent-unique-id='${$parent.data('uniqueId')}']`);

        for (const optionalProduct of $optProducts) {
            const $currentOptionalProduct = $(optionalProduct);
            const childCombination = this.getSelectedVariantValues($currentOptionalProduct);
            const productTemplateId = parseInt($currentOptionalProduct.find('.product_template_id').val());
            ajax.jsonRpc(this._getUri('/sale/get_combination_info'), 'call', {
                'product_template_id': productTemplateId,
                'product_id': this._getProductId($currentOptionalProduct),
                'combination': childCombination,
                'add_qty': parseInt($currentOptionalProduct.find('input[name="add_qty"]').val()),
                'pricelist_id': this.pricelistId || false,
                'parent_combination': combination,
                'context': session.user_context,
                ...this._getOptionalCombinationInfoParam($currentOptionalProduct),
            }).then((combinationData) => {
                if (this._shouldIgnoreRpcResult()) {
                    return;
                }
                this._onChangeCombination(ev, $currentOptionalProduct, combinationData);
                this._checkExclusions($currentOptionalProduct, childCombination, combinationData.parent_exclusions);
            });
        }
    } else {
        parentCombination = this.getSelectedVariantValues(
            $parent.parent().find('.js_product.in_cart.main_product')
        );
    }
    return ajax.jsonRpc(this._getUri('/sale/get_combination_info'), 'call', {
        'product_template_id': parseInt($parent.find('.product_template_id').val()),
        'product_id': this._getProductId($parent),
        'combination': combination,
        'add_qty': parseInt($parent.find('input[name="add_qty"]').val()),
        'pricelist_id': this.pricelistId || false,
        'parent_combination': parentCombination,
        'partner_id': this.context.partner_id,
        'context': session.user_context,
        ...this._getOptionalCombinationInfoParam($parent),
    }).then((combinationData) => {
        if (this._shouldIgnoreRpcResult()) {
            return;
        }
        this._onChangeCombination(ev, $parent, combinationData);
        this._checkExclusions($parent, combination, combinationData.parent_exclusions);
    });
}

return VariantMixin;

});
