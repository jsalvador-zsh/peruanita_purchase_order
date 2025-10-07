from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    # Campo para vincular pagos directamente a órdenes de compra
    purchase_id = fields.Many2one(
        'purchase.order',
        string='Orden de Compra',
        help='Orden de compra asociada a este pago. Útil cuando se registra el pago '
             'antes de la factura y se desea hacer seguimiento.'
    )
    
    # Campo computado para mostrar el estado de la orden vinculada
    purchase_order_name = fields.Char(
        related='purchase_id.name',
        string='Número de O.C.',
        readonly=True
    )
    
    @api.onchange('purchase_id')
    def _onchange_purchase_id(self):
        """
        Cuando se selecciona una orden de compra, autocompletar el proveedor
        y el memo si están vacíos
        """
        if self.purchase_id:
            if not self.partner_id:
                self.partner_id = self.purchase_id.partner_id
            if not self.memo:
                self.memo = f"Pago O.C. {self.purchase_id.name}"
    
    @api.model_create_multi
    def create(self, vals_list):
        """Recalcular estado de pago de la orden cuando se crea un pago"""
        payments = super().create(vals_list)
        # Buscar órdenes de compra que necesitan recalcular
        purchase_orders = payments.mapped('purchase_id')
        if purchase_orders:
            purchase_orders._compute_payment_status()
        return payments
    
    def write(self, vals):
        """Recalcular estado de pago de la orden cuando se modifica un pago"""
        # Guardar órdenes antes del cambio
        old_purchase_orders = self.mapped('purchase_id')
        result = super().write(vals)
        # Buscar órdenes después del cambio
        new_purchase_orders = self.mapped('purchase_id')
        # Recalcular ambas (la antigua y la nueva si cambió)
        all_orders = old_purchase_orders | new_purchase_orders
        if all_orders:
            all_orders._compute_payment_status()
        return result
    
    def unlink(self):
        """Recalcular estado de pago de la orden cuando se elimina un pago"""
        purchase_orders = self.mapped('purchase_id')
        result = super().unlink()
        if purchase_orders:
            purchase_orders._compute_payment_status()
        return result

