/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import VariantMixin from 'sale.VariantMixin';
import core from 'web.core';

const _t = core._t;

patch(VariantMixin, 'product_product_hide_not_available.VariantMixinPatch', {
    _disableInput($parent, attributeValueId, excludedBy, attributeNames, productName) {
        const $input = $parent.find(
            `option[value=${attributeValueId}], input[value=${attributeValueId}]`
        );
        $input.addClass('d-none');
        $input.closest('label').addClass('d-none');
        $input.closest('.o_variant_pills').addClass('d-none');
        if (excludedBy && attributeNames) {
            const $target = $input.is('option') ? $input : $input.closest('label').add($input);
            let excludedByData = [];
            if ($target.data('excluded-by')) {
                excludedByData = JSON.parse($target.data('excluded-by'));
            }
            let excludedByName = attributeNames[excludedBy];
            if (productName) {
                excludedByName = productName + ' (' + excludedByName + ')';
            }
            excludedByData.push(excludedByName);
            $target.attr('title', _.str.sprintf(_t('Not available with %s'), excludedByData.join(', ')));
            $target.data('excluded-by', JSON.stringify(excludedByData));
        }
    },

    _toggleDisable($parent, isCombinationPossible) {
        $parent.toggleClass('d-none', !isCombinationPossible);
        if ($parent.hasClass('in_cart')) {
            const primaryButton = $parent.parents('.modal-content').find('.modal-footer .btn-primary');
            primaryButton.prop('disabled', !isCombinationPossible);
            primaryButton.toggleClass('disabled', !isCombinationPossible);
        }
    },

    _checkExclusions($parent, combination, parentExclusions) {
        $parent
            .find('option, input, label, .o_variant_pills')
            .removeClass('d-none')
            .attr('title', function () { return $(this).data('value_name') || ''; })
            .data('excluded-by', '');
        const combinationData = $parent
            .find('ul[data-attribute_exclusions]')
            .data('attribute_exclusions');
        if (combinationData && combinationData.archived_combinations) {
            for (const excludedCombination of combinationData.archived_combinations) {
                if (excludedCombination.length === 1) {
                    const disabledPtav = excludedCombination[0];
                    this._disableInput(
                        $parent,
                        disabledPtav,
                        false,
                        combinationData.mapped_attribute_names,
                    );
                    return;
                }
            }
        }
        this._super($parent, combination, parentExclusions);
    },
});
