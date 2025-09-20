from odoo import models, fields, api

class MedicalPatient(models.Model):
    _name = 'medical.patient'
    _description = 'Medical Patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Full Name', required=True, tracking=True)
    patient_id = fields.Char(
        string='Patient ID', 
        required=True, 
        copy=False, 
        readonly=True, 
        default='New'
    )
    
    # Personal Information
    birth_date = fields.Date(string='Date of Birth')
    age = fields.Integer(string='Age', compute='_compute_age')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender')
    
    # Contact Information
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    email = fields.Char(string='Email')
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')
    
    # Medical Information
    blood_type = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-')
    ], string='Blood Type')
    
    allergies = fields.Text(string='Allergies')
    medical_history = fields.Text(string='Medical History')
    current_medications = fields.Text(string='Current Medications')
    
    # Emergency Contact
    emergency_contact_name = fields.Char(string='Emergency Contact Name')
    emergency_contact_phone = fields.Char(string='Emergency Contact Phone')
    emergency_relation = fields.Char(string='Relationship')
    
    # Insurance
    insurance_company = fields.Char(string='Insurance Company')
    insurance_number = fields.Char(string='Insurance Number')
    
    # Relations
    appointment_ids = fields.One2many('medical.appointment', 'patient_id', string='Appointments')
    medical_record_ids = fields.One2many('medical.record', 'patient_id', string='Medical Records')
    prescription_ids = fields.One2many('medical.prescription', 'patient_id', string='Prescriptions')
    
    # Computed fields
    appointment_count = fields.Integer(compute='_compute_appointment_count')

    @api.depends('birth_date')
    def _compute_age(self):
        for record in self:
            if record.birth_date:
                today = fields.Date.today()
                record.age = today.year - record.birth_date.year - \
                    ((today.month, today.day) < (record.birth_date.month, record.birth_date.day))
            else:
                record.age = 0

    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        for patient in self:
            patient.appointment_count = len(patient.appointment_ids)

    @api.model
    def create(self, vals):
        if vals.get('patient_id', 'New') == 'New':
            vals['patient_id'] = self.env['ir.sequence'].next_by_code('medical.patient') or 'New'
        return super().create(vals)

    def action_view_appointments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patient Appointments',
            'view_mode': 'tree,form',
            'res_model': 'medical.appointment',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id}
        }