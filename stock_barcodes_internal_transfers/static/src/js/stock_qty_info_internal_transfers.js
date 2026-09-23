/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import { Component, useRef, onMounted } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { usePopover } from "@web/core/popover/popover_hook";

patch(ListRenderer.prototype, "StockInfoWidget", {
    _renderBodyCell(record, node) {
        const $td = super._renderBodyCell(record, node);
        if (node.tag === "widget" && node.attrs.name === "stock_info_widget") {
            $td.classList.add("o_list_button");
        }
        return $td;
    },
});

class StockInfoWidget extends Component {
    setup() {
        this.elRef = useRef("popoverContainer");
        this.popover = usePopover();
        onMounted(() => {
            this._setPopOver();
        });
    }

    _setPopOver() {
        const content = document.createElement("div");
        content.innerHTML = this.env.qweb.render(
            "stock_barcodes_internal_transfers.StockInfoDetails",
            { data: this.props.data }
        );
        this.popover.addPopover({
            target: this.elRef.el,
            content: content,
            title: "Stock",
            placement: "left",
            trigger: "focus",
            delay: { show: 0, hide: 100 },
        });
    }

    _onClickButton() {
        this.elRef.el.querySelector(".fa-info-circle").dataset.special_click = true;
    }
}

StockInfoWidget.template = "stock_barcodes_internal_transfers.StockInfoWidget";
StockInfoWidget.props = {
    data: Object,
};

registry.category("view_widgets").add("stock_info_widget", StockInfoWidget);

export default StockInfoWidget;
