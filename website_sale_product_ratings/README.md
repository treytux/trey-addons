Cómo utilizarlo
---------------

Puede mostrarse el widget activando la opción de personalización "Product
Ratings" tanto desde el listado como desde la ficha de producto.

O bien, no activar dichos widgets e insertar en nuestro código la siguiente
llamada para ubicarlos en cualquier posición dentro de la página:

```xml
    <div class="product_rating">
        <t t-call="website_ratings.widget">
            <t t-set="object_id" t-value="product.id"/>
            <t t-set="object_model">product.template</t>
            <t t-set="ratings" t-value="product.ratings"/>
            <t t-set="numbers_of_ratings"
               t-value="product.numbers_of_ratings"/>
            <t t-set="input_name" t-value="'rating_product_' +
               str(product.id)"/>
        </t>
    </div>
```
