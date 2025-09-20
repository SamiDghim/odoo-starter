from odoo import models, fields, api

class MedicalPrescription(models.Model):
    _name = 'medical.prescription'
    _description = 'Medical Prescription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Prescription Reference', 
        required=True, 
        copy=False, 
        readonly=True, 
        default='New'
    )
    
    patient_id = fields.Many2one('medical.patient', string='Patient', required=True)
    doctor_id = fields.Many2one('medical.doctor', string='Prescribing Doctor', required=True)
    appointment_id = fields.Many2one('medical.appointment', string='Appointment')
    prescription_date = fields.Date(string='Prescription Date', default=fields.Date.today, required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('prescribed', 'Prescribed'),
        ('dispensed', 'Dispensed'),
        ('completed', 'Completed')
    ], string='Status', default='draft', tracking=True)
    
    prescription_line_ids = fields.One2many('medical.prescription.line', 'prescription_id', string='Medications')
    notes = fields.Text(string='Additional Instructions')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('medical.prescription') or 'New'
        return super().create(vals)

class MedicalPrescriptionLine(models.Model):
    _name = 'medical.prescription.line'
    _description = 'Prescription Line'
    _rec_name = 'medication_name'

    prescription_id = fields.Many2one('medical.prescription', string='Prescription', required=True, ondelete='cascade')
    medication_id = fields.Many2one('medical.drug', string='Medication')
    medication_name = fields.Char(string='Medication', required=True)
    dosage = fields.Char(string='Dosage', required=True)
    frequency = fields.Char(string='Frequency', required=True)
    duration = fields.Char(string='Duration', required=True)
    instructions = fields.Text(string='Special Instructions')
    quantity = fields.Float(string='Quantity', default=1.0)

    @api.onchange('medication_id')
    def _onchange_medication_id(self):
        if self.medication_id:
            self.medication_name = self.medication_id.name
            if self.medication_id.default_dosage:
                self.dosage = self.medication_id.default_dosage
            if self.medication_id.default_frequency:
                self.frequency = self.medication_id.default_frequency
            if self.medication_id.default_duration:
                self.duration = self.medication_id.default_duration