/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useSortable } from "@web/core/utils/sortable";
import { BoardController } from "@board/board_controller";
import { BoardArchParser } from "@board/board_view";

const { useRef, useState } = owl;

patch(BoardArchParser.prototype, "board_share.BoardArchParser", {
    parse(arch, customViewId) {
        const archInfo = this._super(...arguments);
        const xmlDoc = new DOMParser().parseFromString(arch, "text/xml");
        const boardNode = xmlDoc.querySelector("board");
        archInfo.shareable = Boolean(
            boardNode && parseInt(boardNode.getAttribute("shareable") || "0", 10)
        );
        archInfo.isReadonly = Boolean(
            boardNode && parseInt(boardNode.getAttribute("readonly") || "0", 10)
        );
        return archInfo;
    },
});

patch(BoardController.prototype, "board_share.BoardController", {
    setup() {
        this.board = useState(this.props.board);
        this.rpc = useService("rpc");
        this.dialogService = useService("dialog");
        this.actionService = useService("action");
        if (this.board.isReadonly) {
            return;
        }
        if (this.env.isSmall) {
            this.selectLayout("1", false);
            return;
        }
        const mainRef = useRef("main");
        useSortable({
            ref: mainRef,
            elements: ".o-dashboard-action",
            handle: ".o-dashboard-action-header",
            cursor: "move",
            groups: ".o-dashboard-column",
            connectGroups: true,
            onDrop: ({ element, previous, parent }) => {
                const fromColIdx = parseInt(
                    element.parentElement.dataset.idx,
                    10,
                );
                const fromActionIdx = parseInt(element.dataset.idx, 10);
                const toColIdx = parseInt(parent.dataset.idx, 10);
                const toActionIdx = previous
                    ? parseInt(previous.dataset.idx, 10) + 1
                    : 0;
                if (fromColIdx !== toColIdx) {
                    element.classList.add("d-none");
                }
                this.moveAction(
                    fromColIdx,
                    fromActionIdx,
                    toColIdx,
                    toActionIdx,
                );
            },
        });
    },

    moveAction() {
        if (this.board.isReadonly) {
            return;
        }
        return this._super(...arguments);
    },

    selectLayout() {
        if (this.board.isReadonly) {
            return;
        }
        return this._super(...arguments);
    },

    closeAction() {
        if (this.board.isReadonly) {
            return;
        }
        return this._super(...arguments);
    },

    toggleAction() {
        if (this.board.isReadonly) {
            return;
        }
        return this._super(...arguments);
    },

    saveBoard() {
        if (this.board.isReadonly) {
            return;
        }
        return this._super(...arguments);
    },

    openShareDialog() {
        if (!this.board.shareable) {
            return;
        }
        this.actionService.doAction({
            name: this.env._t("Share Dashboard"),
            type: "ir.actions.act_window",
            res_model: "board.share.wizard",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_name: this.board.title,
            },
        });
    },
});
