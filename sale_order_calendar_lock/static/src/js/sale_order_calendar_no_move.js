/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CalendarCommonRenderer } from "@web/views/calendar/calendar_common/calendar_common_renderer";

patch(CalendarCommonRenderer.prototype, "sale_order_calendar_lock", {
    convertRecordToEvent(record) {
        const event = this._super.apply(this, arguments);
        if (this.props.model.meta.resModel !== "sale.order") {
            return event;
        }
        const state = record.rawRecord && record.rawRecord.state;
        const isLocked = state !== "draft";
        if (isLocked) {
            event.editable = false;
        }
        return event;
    },
});
