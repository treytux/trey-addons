### Dependencias externas

```
git clone https://github.com/OCA/account-financial-reporting.git -b 11.0
git clone https://github.com/OCA/account-financial-tools.git -b 11.0
git clone https://github.com/OCA/account-invoicing.git -b 11.0
git clone https://github.com/OCA/bank-payment.git -b 11.0
git clone https://github.com/OCA/bank-statement-import.git -b 11.0
git clone https://github.com/OCA/account-payment.git -b 11.0
git clone https://github.com/OCA/l10n-spain.git -b 11.0
git clone https://github.com/OCA/partner-contact -b 11.0
git clone https://github.com/OCA/mis-builder.git -b 11.0
git clone https://github.com/OCA/reporting-engine.git -b 11.0
git clone https://github.com/OCA/server-ux.git -b 11.0
```


### Modulos 8.0 que no se incluyen en 11.0

#### Nuevos modulos para la 11.0
__account_tag_menu:__ Menu de acceso a las etiquetas de cuentas contables y analiticas.

__account_type_menu:__ Menu de acceso a los tipos de cuentas.

__l10n_es_mis_report:__ Informes fiscales oficiales españolas usando mis_builder.

__account_payment_term_extension:__ Mayor configuracion de los dias de pago. Soporta dias fijos de pago.

__account_fiscal_year:__Usando la funcionalidad del modulo date_range define un tipo de
fecha ejercicio fiscal para utilizarlo en los informes etc.

#### Cambiados de nombre
__account_financial_report_webkit_xls:__ Pasa a llamarse account_financial_report
__account_tax_analisys:__ Pasa a llamarse account_tax_balance no con las misma funcionalidad.


#### Pendientes de migrar a la 11.0
__account_renumber:__ No migrado (20/07/2018)
__purchase_fiscal_position_update:__ No migrado (20/07/2018)

#### No disponibles en 11.0
* account_invoice_not_negative
* account_ignvoice_export_xls,  # Rama de factor libre
* account_payment_purchase,
* account_payment_sale_stock
* l10n_es_intrastat_product,  # no mergeado
* l10n_es_patch_country_aeat_mod349,  # desconocido
* account_balance_reporting_xls, # No es necesario con mis_builder
* account_followup,
* account_journal_active,
* account_move_line_tree_without_selectors,
* account_partner_ledger_report,
* account_reconcile_trace,  # Problema query en Naparbier
* account_tax_chart_interval'
* l10n_es_account_balance_report'
