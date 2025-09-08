from odoo import fields, models

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    
    # Tipo de cuenta
    account_type = fields.Selection([
        ('savings', 'Ahorros'),
        ('checking', 'Corriente'),
        ('cts', 'CTS'),
        ('other', 'Otra'),
    ], string='Tipo de Cuenta', default='checking')
    
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
            if hasattr(bank, 'cci_number') and bank.cci_number:
                name += f" (CCI: {bank.cci_number})"
            elif hasattr(bank, 'l10n_pe_cci') and bank.l10n_pe_cci:
                name += f" (CCI: {bank.l10n_pe_cci})"
            result.append((bank.id, name))
        return result