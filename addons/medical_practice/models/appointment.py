from odoo import models, fields, api
from datetime import timedelta

class MedicalAppointment(models.Model):
    _name = 'medical.appointment'
    _description = 'Medical Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'appointment_date desc'

    name = fields.Char(
        string='Appointment Reference', 
        required=True, 
        copy=False, 
        readonly=True, 
        default='New'
    )
    
    patient_id = fields.Many2one('medical.patient', string='Patient', required=True, tracking=True)
    doctor_id = fields.Many2one('res.users', string='Doctor', required=True, tracking=True)
    appointment_date = fields.Datetime(string='Appointment Date/Time', required=True, tracking=True)
    duration = fields.Float(string='Duration (Hours)', default=1.0)
    end_time = fields.Datetime(string='End Time', compute='_compute_end_time', store=True)
    
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show')
    ], string='Status', default='scheduled', tracking=True)
    
    appointment_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('checkup', 'Regular Checkup'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency')
    ], string='Appointment Type', required=True)
    
    reason = fields.Text(string='Reason for Visit')
    notes = fields.Text(string='Doctor Notes')
    
    # Relations
    prescription_ids = fields.One2many('medical.prescription', 'appointment_id', string='Prescriptions')

    @api.depends('appointment_date', 'duration')
    def _compute_end_time(self):
        for appointment in self:
            if appointment.appointment_date and appointment.duration:
                appointment.end_time = appointment.appointment_date + timedelta(hours=appointment.duration)
            else:
                appointment.end_time = False

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('medical.appointment') or 'New'
        return super().create(vals)

    def action_confirm(self):
        self.state = 'confirmed'
        
    def action_start(self):
        self.state = 'in_progress'
        
    def action_complete(self):
        self.state = 'completed'
        
    def action_cancel(self):
        self.state = 'cancelled'