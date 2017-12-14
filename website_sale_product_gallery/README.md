# Website_sale_product_gallery

## Caracteristicas

Modulo para la creacion de galerias de imagenes para product.template y 
atributos de producto.


##WhiteList

* Ahora mismo existe un enlace entre el product.template y los attribute.value, 
esto se salta el estandar de odoo. Podemos utilizar el campo attribute_line_ids
que relaciona los product.template con sus product.attribute y attribute.value.

* En el formulario para agregar imagen, hacer un filtrado de las caracteristicas
para que solo esten disponibles las caracteristicas y valores de caracteristicas
del template y/o sus variantes.
