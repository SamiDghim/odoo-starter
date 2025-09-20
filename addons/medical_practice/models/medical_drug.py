from odoo import models, fields


class MedicalDrug(models.Model):
    _name = 'medical.drug'
    _description = 'Medical Drug / Medication'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Drug Code')
    description = fields.Text(string='Description')
    default_dosage = fields.Char(string='Default Dosage')
    default_frequency = fields.Char(string='Default Frequency')
    default_duration = fields.Char(string='Default Duration')
    active = fields.Boolean(string='Active', default=True)
