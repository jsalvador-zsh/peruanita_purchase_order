from odoo import models, fields, api
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Área solicitante usando departamentos nativos
    requesting_department_id = fields.Many2one(
        'hr.department',
        string='Área Solicitante',
        help='Departamento que solicita la compra'
    )
    
    # Mes de abastecimiento
    supply_month = fields.Selection([
        ('enero', 'ENERO'),
        ('febrero', 'FEBRERO'),
        ('marzo', 'MARZO'),
        ('abril', 'ABRIL'),
        ('mayo', 'MAYO'),
        ('junio', 'JUNIO'),
        ('julio', 'JULIO'),
        ('agosto', 'AGOSTO'),
        ('septiembre', 'SEPTIEMBRE'),
        ('octubre', 'OCTUBRE'),
        ('noviembre', 'NOVIEMBRE'),
        ('diciembre', 'DICIEMBRE'),
    ], string='Mes de Abastecimiento')
    
    # Observaciones
    purchase_observations = fields.Text(
        string='Observaciones'
    )
    
    # Campos de control de firmas
    elaborated_by = fields.Char(
        string='Elaborado Por',
        default=lambda self: self.env.user.name
    )
    
    received_by = fields.Char(
        string='Recibido Por'
    )
    
    # Control de tesorería
    treasury_approval = fields.Boolean(
        string='Aprobado por Tesorería',
        default=False
    )
    
    treasury_approved_by = fields.Char(
        string='Aprobado por (Tesorería)'
    )
    
    # Fechas de cancelación
    cancellation_dates = fields.Text(
        string='Fecha(s) de cancelación'
    )
    
    # Estado de pago
    payment_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('partial', 'Parcial'),
        ('paid', 'Pagado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado de Pago', default='pending')
    
    receipt_status = fields.Selection([
        ('no', 'No Recibido'),
        ('partial', 'Parcialmente Recibido'),
        ('full', 'Totalmente Recibido'),
    ], string='Estado de Recepción', compute='_compute_receipt_status', store=True)
    
    @api.depends('order_line.qty_received', 'order_line.product_qty')
    def _compute_receipt_status(self):
        for order in self:
            if order.state not in ('purchase', 'done'):
                order.receipt_status = 'no'
                continue
                
            # Verificar si hay líneas de producto (no servicios)
            product_lines = order.order_line.filtered(
                lambda l: l.product_id.type in ['product', 'consu']
            )
            
            if not product_lines:
                order.receipt_status = 'no'
                continue
            
            total_ordered = sum(product_lines.mapped('product_qty'))
            total_received = sum(product_lines.mapped('qty_received'))
            
            if total_received == 0:
                order.receipt_status = 'no'
            elif total_received >= total_ordered:
                order.receipt_status = 'full'
            else:
                order.receipt_status = 'partial'

    # Método para generar número de orden personalizado
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self._generate_custom_purchase_number()
        return super(PurchaseOrder, self).create(vals)
    
    def _generate_custom_purchase_number(self):
        """Genera el número de orden en formato YYYY-NNNN"""
        current_year = datetime.now().year
        
        # Buscar la última orden del año actual
        last_order = self.search([
            ('name', 'like', f'{current_year}-')
        ], order='name desc', limit=1)
        
        if last_order and last_order.name:
            try:
                # Extraer el número secuencial
                number_part = last_order.name.split('-')[-1]
                next_number = int(number_part) + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f'{current_year}-{next_number:04d}'
    
    # Método para obtener datos bancarios del proveedor
    def get_supplier_bank_info(self):
        """Retorna información bancaria del proveedor usando cuentas nativas"""
        if self.partner_id and self.partner_id.bank_ids:
            # Buscar cuenta principal o tomar la primera
            main_account = self.partner_id.bank_ids.filtered('is_main_account')
            if not main_account:
                main_account = self.partner_id.bank_ids[0]
            
            return {
                'bank_name': main_account.bank_id.name if main_account.bank_id else '',
                'account_number': main_account.acc_number or '',
                'cci_number': main_account.cci_number or '',
                'account_type': dict(main_account._fields['account_type'].selection).get(main_account.account_type, '') if hasattr(main_account, 'account_type') else '',
            }
        return {
            'bank_name': '',
            'account_number': '',
            'cci_number': '',
            'account_type': '',
        }
    
    # Método para obtener contacto de compras del proveedor
    def get_purchase_contact_info(self):
        """Retorna información del contacto de compras usando contactos relacionados"""
        if self.partner_id:
            # Buscar contacto específico para compras
            purchase_contact = self.partner_id.child_ids.filtered(
                lambda c: c.function and 'compra' in c.function.lower()
            )
            
            if purchase_contact:
                contact = purchase_contact[0]
                return {
                    'name': contact.name,
                    'phone': contact.phone or contact.mobile or self.partner_id.phone,
                    'email': contact.email or self.partner_id.email,
                }
            else:
                # Usar datos del proveedor principal
                return {
                    'name': self.partner_id.name,
                    'phone': self.partner_id.phone or self.partner_id.mobile,
                    'email': self.partner_id.email,
                }
        return {
            'name': '',
            'phone': '',
            'email': '',
        }
    
    # Método para marcar como aprobado por tesorería
    def approve_by_treasury(self):
        """Marca la orden como aprobada por tesorería"""
        self.write({
            'treasury_approval': True,
            'treasury_approved_by': self.env.user.name,
        })
    
    # Método para registrar fecha de cancelación
    def register_payment_date(self, payment_date=None):
        """Registra una fecha de pago/cancelación"""
        if not payment_date:
            payment_date = fields.Date.today()
        
        current_dates = self.cancellation_dates or ''
        new_date = f"{payment_date.strftime('%d/%m/%Y')}"
        
        if current_dates:
            self.cancellation_dates = f"{current_dates}, {new_date}"
        else:
            self.cancellation_dates = new_date
    
    # Campos computados para el reporte
    @api.depends('date_order')
    def _compute_formatted_date(self):
        for record in self:
            if record.date_order:
                date = fields.Datetime.from_string(record.date_order)
                record.formatted_date = date.strftime('%d/%m/%y')
            else:
                record.formatted_date = ""
    
    formatted_date = fields.Char(
        string='Fecha Formateada',
        compute='_compute_formatted_date',
        store=True
    )

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    receipt_status_line = fields.Selection([
        ('no', 'No Recibido'),
        ('partial', 'Parcialmente Recibido'),
        ('full', 'Totalmente Recibido'),
    ], string='Estado Recepción', compute='_compute_receipt_status_line', store=True)
    
    @api.depends('qty_received', 'product_qty')
    def _compute_receipt_status_line(self):
        for line in self:
            if line.product_id.type not in ['product', 'consu']:
                line.receipt_status_line = 'no'
                continue
                
            if line.qty_received == 0:
                line.receipt_status_line = 'no'
            elif line.qty_received >= line.product_qty:
                line.receipt_status_line = 'full'
            else:
                line.receipt_status_line = 'partial'