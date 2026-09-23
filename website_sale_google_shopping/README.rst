============================
Website Sale Google Shopping
============================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

This module generates a product feed for **Google Merchant Center** directly from your Odoo e-commerce. It allows you to index your products in Google Shopping with specific attributes required by Google.

**Features:**

* Generates an XML feed compatible with Google Merchant Center.
* Supports product variants (Color, Size, Material, Pattern).
* Maps Odoo fields to Google Shopping attributes (Availability, Condition, Gender, Age Group, etc.).
* Includes Google Product Taxonomy import.
* Configurable feed settings per Website.

Google Merchant Center Help
===========================

For more information about Google Merchant Center specifications, please refer to the official documentation:

* **Products Feed Specification:**
  https://support.google.com/merchants/answer/188494

* **Troubleshooting:**
  https://support.google.com/merchants/answer/160161

* **Categorize your products:**
  https://support.google.com/merchants/answer/1705911

Installation
============

To install this module, you need the following dependencies:

1.  Standard Odoo modules: ``website_sale``, ``stock``.
2.  **OCA Product Attribute module**: ``product_brand``.
    * Repository: https://github.com/OCA/brand
    * Make sure this module is available in your addons path.

Configuration
=============

Global Settings
---------------

Go to **Website > Configuration > Websites** and select the website you want to configure. You will find a new tab called **"Google Shopping"** inside the configuration form:

* **Feed size:** Number of products to include (0 for unlimited).
* **Feed expiry time:** Hours to keep the feed cached (default 24h).
* **Image size:** Dimensions for the product images in the feed (default 800x800).
* **Shipping settings:** Define default shipping country, service, and price (optional if configured in Merchant Center).

Product Categories (Taxonomy)
-----------------------------

The module automatically imports Google Product Taxonomies on installation (based on the system language). You can view them at:

* **Website > Configuration > eCommerce > Google product categories**

Usage
=====

Product Configuration
---------------------

To include a product in the feed, ensure:

1.  The product is **Published** on the website.
2.  The product can be sold (`sale_ok = True`).

Go to the product form (Product Template), navigate to the **"Google Shopping"** tab, and configure the specific fields:

* **Google Product Category:** Select the official Google taxonomy category.
* **Condition:** New, Refurbished, or Used.
* **Target Attributes:** Gender, Age Group.
* **Variant Attributes:** Map your Odoo attributes (Color, Size, Material) to Google's requirements.

Generating the Feed
-------------------

Once configured, your feed is available at the following URL:

``http://yourdomain.com/google-shopping.xml``

You can submit this URL to your Google Merchant Center account as a **Scheduled Fetch** feed.

Field Mapping
=============

The module maps Odoo fields to Google Shopping attributes as follows:

* **g:id**: Product ID + Variant ID
* **g:title**: Product Name (+ Variant Attributes)
* **g:description**: Sales Description
* **g:link**: Product Website URL
* **g:image_link**: Product Image URL (resized)
* **g:condition**: Google Shopping Tab > Condition
* **g:availability**: Computed based on stock (In stock / Out of stock / Preorder)
* **g:price**: Product List Price
* **g:brand**: Product Brand (from ``product_brand`` module)
* **g:google_product_category**: Google Shopping Tab > Categories
* **g:product_type**: Odoo eCommerce Category (Public Category)
* **g:gtin**: Barcode field (EAN13)
* **g:mpn**: Google Shopping Tab > Manufacturer Part Number
* **g:item_group_id**: Product Template ID (groups variants together)

Known Issues / Roadmap
======================

* Unit pricing (unit pricing measure, unit pricing base measure) support.
* Energy efficiency labels (EU/Switzerland) support.

Credits
=======

Authors
~~~~~~~

* Trey (https://www.trey.es)

Maintainers
~~~~~~~~~~~

This module is maintained by Trey.
