from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Campo para identificar si es un proveedor principal
    is_main_supplier = fields.Boolean(
        string='Proveedor Principal',
        default=False,
        help='Marca si este contacto es un proveedor principal'
    )
    
    # Días de entrega habitual usando campo nativo
    supplier_delivery_days = fields.Integer(
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
    
    # Método para obtener la cuenta bancaria principal
    def get_main_bank_account(self):
        """Retorna la cuenta bancaria principal del proveedor"""
        if self.bank_ids:
            # Buscar cuenta marcada como principal
            main_account = self.bank_ids.filtered('is_main_account')
            if not main_account:
                main_account = self.bank_ids[0]  # Primera cuenta como principal
            
            return {
                'bank_name': main_account.bank_id.name if main_account.bank_id else 'N/A',
                'account_number': main_account.acc_number or 'N/A',
                'cci_number': main_account.cci_number or 'N/A',
                'account_type': dict(main_account._fields['account_type'].selection).get(main_account.account_type, 'N/A') if hasattr(main_account, 'account_type') else 'N/A',
            }
        return {
            'bank_name': 'N/A',
            'account_number': 'N/A', 
            'cci_number': 'N/A',
            'account_type': 'N/A',
        }
    
    # Método para obtener información completa del contacto de compras
    def get_purchase_contact_info(self):
        """Retorna información del contacto para compras usando contactos relacionados"""
        # Buscar contacto específico para compras
        purchase_contact = self.child_ids.filtered(
            lambda c: c.function and 'compra' in c.function.lower()
        )
        
        if purchase_contact:
            contact = purchase_contact[0]
            return {
                'name': contact.name,
                'phone': contact.phone or contact.mobile or self.phone,
                'email': contact.email or self.email,
            }
        else:
            # Usar datos del contacto principal
            return {
                'name': self.name,
                'phone': self.phone or self.mobile,
                'email': self.email,
            }
    
    # Validación de RUC/DNI
    @api.constrains('vat')
    def _check_vat_format(self):
        for partner in self:
            if partner.vat and partner.country_id and partner.country_id.code == 'PE':
                # Validación básica
                if len(partner.vat) not in [8, 11]:  # DNI: 8 dígitos, RUC: 11 dígitos
                    pass
    
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