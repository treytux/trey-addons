/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useSetupAction } from "@web/webclient/actions/action_hook";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { View } from "@web/views/view";
import { GraphRenderer } from "@web/views/graph/graph_renderer";
import { graphView } from "@web/views/graph/graph_view";

const { Component, onWillStart, useState, useSubEnv } = owl;

class RentalForecastGraphRenderer extends GraphRenderer {}
RentalForecastGraphRenderer.template =
  "rental_availability_forecast.RentalForecastGraphRenderer";

export const RentalForecastGraphView = {
  ...graphView,
  Renderer: RentalForecastGraphRenderer,
};
registry
  .category("views")
  .add("rental_forecast_graph", RentalForecastGraphView);

class RentalForecasted extends Component {
  setup() {
    useSetupAction();
    useSubEnv({
      searchModel: {
        searchMenuTypes: [],
      },
    });
    this.env.config.viewSwitcherEntries = [];
    this.orm = useService("orm");
    this.action = useService("action");
    this.context = this.props.action.context || {};
    this.productId = this.context.active_id;
    this.docs = useState({
      events: [],
      warehouses: [],
      warehouseId: this.context.warehouse || false,
    });
    onWillStart(() => this._load());
  }

  async _load() {
    const warehouses = await this.orm.searchRead(
      "stock.warehouse",
      [
        ["company_id", "=", this.context.allowed_company_ids[0]],
        ["rental_in_location_id", "!=", false],
      ],
      ["id", "display_name"],
      { order: "name,id" },
    );
    this.docs.warehouses = warehouses;
    if (!this.docs.warehouseId && warehouses.length) {
      this.docs.warehouseId = warehouses[0].id;
    }
    if (!this.docs.warehouseId) {
      this.docs.events = [];
      return;
    }
    await this.orm.call("rental.forecast", "generate_for_product_warehouse", [
      this.productId,
      this.docs.warehouseId,
    ]);
    const events = await this.orm.searchRead(
      "rental.forecast.event",
      [
        ["product_id", "=", this.productId],
        ["warehouse_id", "=", this.docs.warehouseId],
      ],
      [
        "event_date",
        "event_type",
        "quantity_change",
        "rental_id",
        "sale_order_line_id",
        "stock_move_id",
        "description",
      ],
      { order: "event_date,id" },
    );
    this.docs.events = events;
  }

  async selectWarehouse(event) {
    this.docs.warehouseId = Number(event.target.value) || false;
    await this._load();
  }

  get graphDomain() {
    return [
      ["product_id", "=", this.productId],
      ["warehouse_id", "=", this.docs.warehouseId],
    ];
  }

  eventType(event) {
    return (
      {
        rental_start: "Rental start",
        rental_return: "Rental return",
        confirmed_rental: "Confirmed rental",
        stock_out: "Stock outgoing",
      }[event.event_type] || event.event_type
    );
  }

  eventClass(event) {
    if (event.event_type === "rental_return") {
      return "table-success";
    }
    if (
      ["rental_start", "confirmed_rental", "stock_out"].includes(
        event.event_type,
      )
    ) {
      return "table-danger";
    }
    return "";
  }

  sourceName(event) {
    const source =
      event.rental_id || event.sale_order_line_id || event.stock_move_id;
    return source ? source[1] : "";
  }

  async openSource(event) {
    if (event.rental_id) {
      return this.action.doAction({
        type: "ir.actions.act_window",
        res_model: "sale.rental",
        res_id: event.rental_id[0],
        views: [[false, "form"]],
      });
    }
    if (event.sale_order_line_id) {
      return this.action.doAction({
        type: "ir.actions.act_window",
        res_model: "sale.order",
        res_id: event.sale_order_line_id[0],
        views: [[false, "form"]],
      });
    }
    if (event.stock_move_id) {
      return this.action.doAction({
        type: "ir.actions.act_window",
        res_model: "stock.move",
        res_id: event.stock_move_id[0],
        views: [[false, "form"]],
      });
    }
  }

  async refresh() {
    await this._load();
  }
}

RentalForecasted.template = "rental_availability_forecast.RentalForecasted";
RentalForecasted.components = { ControlPanel, View };
registry.category("actions").add("rental_replenish_report", RentalForecasted);
