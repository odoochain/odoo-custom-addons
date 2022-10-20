##############################################################################
#
#    Copyright (C) 2022 Didotech SRL
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('payment_term_id')
    def _onchange_payment_term_id_extended(self):
        if self.type == 'out_invoice' and self.state in ['draft']:

            payment_term_model = self.env['account.payment.term']
            spese_incasso = payment_term_model.browse(self.payment_term_id.id)
            product_charges_ids = self._product_charges_ids()
            if self.payment_term_id:
                if self.invoice_line_ids:
                    for line in self.invoice_line_ids:
                        if line.product_id.id in product_charges_ids:
                            self.invoice_line_ids -= line

            if spese_incasso and spese_incasso.spese_incasso_id:
                vals = self._spese_incasso_vals(spese_incasso.spese_incasso_id)
                spese = self.env['account.invoice.line'].new(vals)

    def _payment_term_charges_ids(self):
        records = self.env['account.payment.term'].search([('spese_incasso_id', '!=', False)])
        return [record.id for record in records]

    def _product_charges_ids(self):
        records = self.env['account.payment.term'].search([('spese_incasso_id', '!=', False)])
        products = [item.spese_incasso_id for item in records]
        return [product.id for product in products]

    def _spese_incasso_vals(self, product):
        tax_id = product.taxes_id.id
        account_invoice_line_vals = {
            'invoice_id': self.id,
            'product_id': product.id,
            'name': product.name,
            'account_id': product.property_account_income_id.id,
            'quantity': 1.0,
            'uom_id': product.uom_id.id,
            'price_unit': product.lst_price,
            'invoice_line_tax_ids': [(6, 0, [tax_id])],
        }
        return account_invoice_line_vals

    @api.model
    def create(self, vals):
        """
        check on charges from payment term
        """
        res_id = super().create(vals)
        if res_id.type == 'out_invoice' and res_id.state == 'draft' and res_id.payment_term_id and (
                res_id.payment_term_id.spese_incasso_id):
            payment_term_model = self.env['account.payment.term']
            spese_incasso = payment_term_model.browse(res_id.payment_term_id.id)
            product_charges_ids = res_id._product_charges_ids()
            if res_id.invoice_line_ids:
                for line in res_id.invoice_line_ids:
                    if line.product_id.id in product_charges_ids:
                        res_id.invoice_line_ids -= line

            vals = res_id._spese_incasso_vals(spese_incasso.spese_incasso_id)
            spese = self.env['account.invoice.line'].new(vals)
            res_id.invoice_line_ids += spese

        return res_id