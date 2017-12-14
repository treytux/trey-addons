### Module email custom templates

This module allows to customize email templates.

Templates that need to be replaced in customized modules (not included in this module).

```
Sale Order:
<record id="sale.email_template_edi_sale" model="email.template">
    <field name="name">Sales Order - Send by Email (Custom)</field>
    <field name="body_html">
        <![CDATA[ Contenido a reemplazar sale ]]>
    </field>
</record>

<record id="portal_sale.email_template_edi_sale" model="email.template">
    <field name="name">Sales Order - Send by Email (Portal Custom)</field>
    <field name="body_html">
        <![CDATA[ Contenido a reemplazar portal sale ]]>
    </field>
</record>

Invoice:
<record id="account.email_template_edi_invoice" model="email.template">
    <field name="name">Invoice - Send by Email (Custom)</field>
    <field name="body_html">
        <![CDATA[ Contenido a reemplazar invoice ]]>
    </field>
</record>

<record id="portal_sale.email_template_edi_invoice" model="email.template">
    <field name="name">Invoice - Send by Email (Portal Custom)</field>
    <field name="body_html">
        <![CDATA[ Contenido a reemplazar portal invoice ]]>
    </field>
</record>


Website:
<record id="auth_signup.reset_password_email" model="email.template">
    <field name="name">Reset Password (Custom)</field>
    <field name="body_html">
        <![CDATA[ Contenido a reemplazar reset password ]]>
    </field>
</record>

<record id="auth_signup.set_password_email" model="email.template">
    <field name="name">Odoo Enterprise Connection (Custom)</field>
    <field name="body_html">
        <![CDATA[ Contenido a reemplazar set password ]]>
    </field>
</record>

<template id="email_formats_portal.wizard_user_subject">
    Contenido a reemplazar (asunto datos cuenta)
</template>
<template id="email_formats_portal.wizard_user_body_html">
    Contenido a reemplazar (datos cuenta)
</template>


```
