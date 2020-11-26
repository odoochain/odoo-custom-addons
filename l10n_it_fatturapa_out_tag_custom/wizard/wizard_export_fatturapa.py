# Copyright 2020 Andrei Levin - Didotech srl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
# from odoo.tools.translate import _
# import inspect
import logging
import base64
from odoo.addons.l10n_it_fatturapa.bindings.fatturapa import (
    DatiDocumentiCorrelatiType,
    CodiceArticoloType
)
from odoo.addons.l10n_it_fatturapa_out.wizard.wizard_export_fatturapa import fatturapaBDS
_logger = logging.getLogger(__name__)


class WizardExportFatturapa(models.TransientModel):
    _inherit = "wizard.export.fatturapa"

    def saveAttachment(self, fatturapa, number):
        # curframe = inspect.currentframe()
        # invoices = inspect.getouterframes(curframe, 2)[1].frame.f_locals['invoices']
        # partner = invoices[0].partner_id
        #
        # if partner.xml_dialect:
        #     fatturapa = self.set_custom_tags(fatturapa, invoices[0])
        #
        # return super().saveAttachment(fatturapa, number)

        attach_obj = self.env['fatturapa.attachment.out']
        vat = attach_obj.get_file_vat()

        # attach_str = fatturapa.toxml(
        #     encoding="UTF-8",
        #     bds=fatturapaBDS,
        # )
        attach_str = fatturapa.toDOM().toprettyxml(
            encoding="UTF-8",
            # bds=fatturapaBDS,
        )
        fatturapaBDS.reset()
        attach_vals = {
            'name': '%s_%s.xml' % (vat, number),
            'datas_fname': '%s_%s.xml' % (vat, number),
            'datas': base64.encodestring(attach_str),
        }
        return attach_obj.create(attach_vals)

    def setDatiOrdineAcquisto(self, inv, body):
        if inv.partner_id.xml_dialect in ('amazon',):
            # 2.1.2.2 <IdDocumento>
            body.DatiGenerali.DatiOrdineAcquisto.append(DatiDocumentiCorrelatiType(
                IdDocumento=inv.customer_reference
            ))

    def setFatturaElettronicaBody(self, inv, FatturaElettronicaBody):
        super().setFatturaElettronicaBody(inv, FatturaElettronicaBody)
        self.setDatiOrdineAcquisto(inv, FatturaElettronicaBody)

    def setDettaglioLinea(self, line_no, line, body, price_precision, uom_precision):
        DettaglioLinea = super().setDettaglioLinea(line_no, line, body, price_precision, uom_precision)

        if not line.product_id.barcode:
            customerinfo = self.env['product.customerinfo'].search([
                ('product_id', '=', line.product_id.id),
                ('name', '=', line.invoice_id.partner_id.id)
            ])

            for info in customerinfo:
                CodiceArticolo = CodiceArticoloType(
                    CodiceTipo=info[0].product_code_type,
                    CodiceValore=info[0].product_code[:35]
                )
                DettaglioLinea.CodiceArticolo.append(CodiceArticolo)

        return DettaglioLinea
