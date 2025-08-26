from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Campo para identificar si es un proveedor principal
    is_main_supplier = fields.Boolean(
        string='Proveedor Principal',
        default=False,
        help='Marca si este contacto es un proveedor principal'
    )
    
    # Contacto principal para órdenes de compra
    purchase_contact_name = fields.Char(
        string='Contacto de Compras',
        help='Nombre del contacto principal para órdenes de compra'
    )
    
    # Teléfono específico para compras
    purchase_phone = fields.Char(
        string='Teléfono de Compras',
        help='Teléfono específico para coordinar compras'
    )
    
    # Email específico para compras
    purchase_email = fields.Char(
        string='Email de Compras',
        help='Email específico para envío de órdenes de compra'
    )
    
    # Términos de pago preferidos
    preferred_payment_terms = fields.Selection([
        ('contado', 'AL CONTADO'),
        ('credito_15', 'CRÉDITO 15 DÍAS'),
        ('credito_30', 'CRÉDITO 30 DÍAS'),
        ('credito_45', 'CRÉDITO 45 DÍAS'),
        ('credito_60', 'CRÉDITO 60 DÍAS'),
        ('adelanto_50', 'ADELANTO 50%'),
        ('adelanto_100', 'ADELANTO 100%'),
    ], string='Términos de Pago Preferidos')
    
    # Días de entrega habitual
    delivery_days = fields.Integer(
        string='Días de Entrega',
        default=7,
        help='Número de días habituales para entrega'
    )
    
    # Notas específicas del proveedor
    supplier_notes = fields.Text(
        string='Notas del Proveedor',
        help='Notas específicas sobre este proveedor'
    )
    
    # Estado del proveedor
    supplier_status = fields.Selection([
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('blacklist', 'Lista Negra'),
        ('evaluation', 'En Evaluación'),
    ], string='Estado del Proveedor', default='active')
    
    # Calificación del proveedor
    supplier_rating = fields.Selection([
        ('excellent', 'Excelente'),
        ('good', 'Bueno'),
        ('regular', 'Regular'),
        ('poor', 'Deficiente'),
    ], string='Calificación')
    
    # Método para obtener la cuenta bancaria principal
    def get_main_bank_account(self):
        """Retorna la cuenta bancaria principal del proveedor"""
        if self.bank_ids:
            main_account = self.bank_ids[0]  # Primera cuenta como principal
            return {
                'bank_name': main_account.bank_id.name if main_account.bank_id else 'N/A',
                'account_number': main_account.acc_number or 'N/A',
                'cci_number': getattr(main_account, 'l10n_pe_cci', 'N/A') or 'N/A',
            }
        return {
            'bank_name': 'N/A',
            'account_number': 'N/A', 
            'cci_number': 'N/A',
        }
    
    # Método para obtener información completa del contacto de compras
    def get_purchase_contact_info(self):
        """Retorna información completa del contacto para compras"""
        return {
            'name': self.purchase_contact_name or self.name,
            'phone': self.purchase_phone or self.phone,
            'email': self.purchase_email or self.email,
        }
    
    # Validación de RUC/DNI
    @api.constrains('vat')
    def _check_vat_format(self):
        for partner in self:
            if partner.vat and partner.country_id and partner.country_id.code == 'PE':
                # Validación básica para Perú
                if len(partner.vat) not in [8, 11]:  # DNI: 8 dígitos, RUC: 11 dígitos
                    pass  # Validación suave, no bloquear registro
    
    # Filtros y búsquedas mejoradas
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=100, order=None):
        """Permite buscar proveedores por RUC además del nombre"""
        if domain is None:
            domain = []
        
        # Búsqueda normal
        result = super(ResPartner, self)._name_search(
            name, domain=domain, operator=operator, limit=limit, order=order
        )
        
        if name and len(result) < limit:
            # Búsqueda adicional por RUC/DNI
            vat_domain = domain + [('vat', operator, name)]
            vat_results = self._search(vat_domain, limit=limit-len(result), order=order)
            vat_results = self.browse(vat_results).name_get()
            
            # Combinar resultados evitando duplicados
            existing_ids = {r[0] for r in result}
            for vat_result in vat_results:
                if vat_result[0] not in existing_ids:
                    result.append(vat_result)
        
        return result


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    
    # Campo para CCI específico de Perú
    l10n_pe_cci = fields.Char(
        string='CCI',
        help='Código de Cuenta Interbancaria - Perú'
    )
    
    # Tipo de cuenta
    account_type = fields.Selection([
        ('savings', 'Ahorros'),
        ('checking', 'Corriente'),
        ('cts', 'CTS'),
        ('other', 'Otra'),
    ], string='Tipo de Cuenta', default='checking')
    
    # Moneda de la cuenta
    currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )
    
    # Cuenta principal
    is_main_account = fields.Boolean(
        string='Cuenta Principal',
        default=False
    )
    
    # Método para formato de visualización de cuenta
    def name_get(self):
        result = []
        for bank in self:
            name = f"{bank.bank_id.name if bank.bank_id else 'Banco'} - {bank.acc_number or 'Sin número'}"
            if bank.l10n_pe_cci:
                name += f" (CCI: {bank.l10n_pe_cci})"
            result.append((bank.id, name))
        return result