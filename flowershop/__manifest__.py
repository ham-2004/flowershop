{
    'name': "Flower Shop",
    'summary': "Flower Shop App for Sally",
    'description': """
    App that Helps Keep Track of Every Flower
    """,

    'author': "Tasis Tech",

    'category': 'Uncategorized',
    'version': '17.0.0.0',

    'depends': ['base', 'sale_management', 'stock', 'website_sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/flower.xml',
        'views/product.xml',
        'views/water.xml',
        'views/website_sale.xml',
        'reports/flower_sale_order_views.xml',
        'data/ir_config_parameter.xml',
        'data/actions.xml',
    ],

    'application': True,
    'license': 'LGPL-3',
}

