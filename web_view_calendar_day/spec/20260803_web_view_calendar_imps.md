# Spec: web_view_calendar_imps

## Context

This document describes the changes introduced in the
`web_view_calendar_imps` branch of the `web_view_calendar_day` module
compared to the `12.0` base version.

## Objective

Allow the color of calendar events to be customized according to the analytic
account associated with the event's project.

## Functional changes

### Calendar colors

`account.analytic.account` is extended with `calendar_color`.

- The value accepts three- or six-character hexadecimal color codes.
- The color is applied to events linked to projects whose analytic account has
  a configured color.
- If no color is configured, `#3d86ac` is used.

## Technical changes

- Models for analytic accounts, events, actions, views, and contacts are added.
- The `wizards/wizard_calendar_event.py` wizard and its XML view are added.
- The controller, model, renderer, view, QWeb templates, and SCSS styles for
  the daily view are added.
- XML views for events, analytic accounts, contacts, and assets are added.
- The manifest is updated with the module dependencies and data.
