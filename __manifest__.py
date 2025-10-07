{
    'name': 'Personalización Módulo de Compras - PERUANITA',
    'version': '18.0.1.0.3',
    'category': 'Purchases',
    'summary': 'Personalización del módulo de compras para formato de órdenes específico',
    'description': """
        Módulo de personalización para el sistema de compras que incluye:
        - Campos personalizados en órdenes de compra
        - Área solicitante y mes de abastecimiento
        - Datos bancarios de proveedores
        - Plantilla de PDF personalizada para órdenes de compra
        - Campos de control y seguimiento
        - Proceso de cancelación y tesorería
    """,
    'author': 'Juan Salvador',
    'website': 'https://jsalvador.dev',
    'depends': [
        'base',
        'purchase',
        'purchase_stock',
        'account',
        'peruanita_sale_order',
        'contacts'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_bank_views.xml',
        'views/res_partner_views.xml',
        'views/purchase_order_views.xml',
        'views/account_payment_views.xml',
        'reports/purchase_order_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}