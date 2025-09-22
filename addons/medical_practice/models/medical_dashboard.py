from odoo import models, fields, api
from xml.sax.saxutils import escape as xml_escape
import math


class MedicalDashboard(models.Model):
    _name = 'medical.dashboard'
    _description = 'Tableau de bord médical'

    name = fields.Char(string="Dashboard", default="Medical Dashboard")

    # Smart Buttons
    patient_count = fields.Integer(string="Total Patients", compute="_compute_counts")
    doctor_count = fields.Integer(string="Total Doctors", compute="_compute_counts")
    appointment_count = fields.Integer(string="Total Appointments", compute="_compute_counts")
    prescriptions_count = fields.Integer(string="Total Ordonnances", compute="_compute_counts")

    @api.depends()
    def _compute_counts(self):
        for record in self:
            record.patient_count = self.env['medical.patient'].search_count([])
            record.doctor_count = self.env['medical.doctor'].search_count([])
            record.appointment_count = self.env['medical.appointment'].search_count([])
            record.prescriptions_count = self.env['medical.prescription'].search_count([])


    # Dashboard actions used by the smart buttons in the view
    def action_open_patients(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patients',
            'res_model': 'medical.patient',
            'view_mode': 'tree,form',
            'domain': [],
        }

    def action_open_doctors(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Doctors',
            'res_model': 'medical.doctor',
            'view_mode': 'tree,form',
            'domain': [],
        }

    def action_open_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'res_model': 'medical.appointment',
            'view_mode': 'calendar,tree,form',
            'domain': [],
        }

    def action_open_prescriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Prescriptions',
            'res_model': 'medical.prescription',
            'view_mode': 'tree,form',
            'domain': [],
        }

    # Safe action-returning helpers (use env.ref to read existing actions by external id)
    def open_patients_graph(self):
        self.ensure_one()
        action = self.env.ref('medical_practice.action_patients_per_doctor', False)
        return action.read()[0] if action else {'type': 'ir.actions.act_window', 'res_model': 'medical.patient', 'view_mode': 'graph'}

    def open_bloodtype_pie(self):
        self.ensure_one()
        action = self.env.ref('medical_practice.action_patient_bloodtype_pie', False)
        return action.read()[0] if action else {'type': 'ir.actions.act_window', 'res_model': 'medical.patient', 'view_mode': 'graph'}

    def open_patients_week_graph(self):
        self.ensure_one()
        action = self.env.ref('medical_practice.action_patients_per_week', False)
        return action.read()[0] if action else {'type': 'ir.actions.act_window', 'res_model': 'medical.patient', 'view_mode': 'graph'}

    def open_prescriptions_doctor_graph(self):
        self.ensure_one()
        action = self.env.ref('medical_practice.action_prescriptions_per_doctor', False)
        return action.read()[0] if action else {'type': 'ir.actions.act_window', 'res_model': 'medical.prescription', 'view_mode': 'graph'}

    def open_prescriptions_month_graph(self):
        self.ensure_one()
        action = self.env.ref('medical_practice.action_prescriptions_per_month', False)
        return action.read()[0] if action else {'type': 'ir.actions.act_window', 'res_model': 'medical.prescription', 'view_mode': 'graph'}

