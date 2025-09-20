from odoo import models, fields, api

class MedicalRecord(models.Model):
    _name = 'medical.record'
    _description = 'Medical Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'record_date desc'

    name = fields.Char(
        string='Record Reference', 
        required=True, 
        copy=False, 
        readonly=True, 
        default='New'
    )
    
    patient_id = fields.Many2one('medical.patient', string='Patient', required=True, tracking=True)
    doctor_id = fields.Many2one('medical.doctor', string='Doctor', required=True)
    appointment_id = fields.Many2one('medical.appointment', string='Related Appointment')
    record_date = fields.Datetime(string='Record Date', default=fields.Datetime.now, required=True)
    
    # Vital Signs
    temperature = fields.Float(string='Temperature (°C)')
    blood_pressure_systolic = fields.Integer(string='BP Systolic (mmHg)')
    blood_pressure_diastolic = fields.Integer(string='BP Diastolic (mmHg)')
    heart_rate = fields.Integer(string='Heart Rate (bpm)')
    weight = fields.Float(string='Weight (kg)')
    height = fields.Float(string='Height (cm)')
    bmi = fields.Float(string='BMI', compute='_compute_bmi', store=True)
    
    # Medical Information
    chief_complaint = fields.Text(string='Chief Complaint')
    history_present_illness = fields.Text(string='History of Present Illness')
    physical_examination = fields.Text(string='Physical Examination')
    diagnosis = fields.Text(string='Diagnosis')
    treatment_plan = fields.Text(string='Treatment Plan')
    follow_up_instructions = fields.Text(string='Follow-up Instructions')

    @api.depends('weight', 'height')
    def _compute_bmi(self):
        for record in self:
            if record.weight and record.height:
                height_m = record.height / 100
                record.bmi = record.weight / (height_m ** 2)
            else:
                record.bmi = 0.0

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('medical.record') or 'New'
        return super().create(vals)