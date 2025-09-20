from odoo import models, fields

class MedicalDashboard(models.Model):
    _name = 'medical.dashboard'
    _description = 'Tableau de bord médical'

    name = fields.Char(string="Dashboard", default="Medical Dashboard")

    patient_count = fields.Integer(string="Patients", compute="_compute_counts")
    appointment_count = fields.Integer(string="Rendez-vous", compute="_compute_counts")

    def _compute_counts(self):
        self.patient_count = self.env['medical.patient'].search_count([])
        self.appointment_count = self.env['medical.appointment'].search_count([])

    def action_open_patients(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patients',
            'res_model': 'medical.patient',
            'view_mode': 'tree,form',
        }

    def action_open_appointments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rendez-vous',
            'res_model': 'medical.appointment',
            'view_mode': 'calendar,tree,form',
        }
