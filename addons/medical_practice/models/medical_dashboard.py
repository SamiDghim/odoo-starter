from odoo import models, fields, api
from xml.sax.saxutils import escape as xml_escape


class MedicalDashboard(models.Model):
    _name = 'medical.dashboard'
    _description = 'Tableau de bord médical'

    name = fields.Char(string="Dashboard", default="Medical Dashboard")

    # Smart Buttons
    patient_count = fields.Integer(string="Total Patients", compute="_compute_counts")
    doctor_count = fields.Integer(string="Total Doctors", compute="_compute_counts")
    appointment_count = fields.Integer(string="Total Appointments", compute="_compute_counts")
    prescriptions_count = fields.Integer(string="Total Ordonnances", compute="_compute_counts")

    # Chart Field
    doctor_patient_chart = fields.Html(string="Doctor-Patient Chart", compute="_compute_doctor_patient_chart")
    doctor_patient_chart_url = fields.Char(string='Doctor Patient Chart URL', compute='_compute_doctor_patient_chart')

    @api.depends()
    def _compute_counts(self):
        for record in self:
            record.patient_count = self.env['medical.patient'].search_count([])
            record.doctor_count = self.env['medical.doctor'].search_count([])
            record.appointment_count = self.env['medical.appointment'].search_count([])
            record.prescriptions_count = self.env['medical.prescription'].search_count([])

    @api.depends()
    def _compute_doctor_patient_chart(self):
        for record in self:
            # Only include active doctors
            doctors = self.env['medical.doctor'].search([('active', '=', True)])
            chart_data = []
            for doctor in doctors:
                appts = self.env['medical.appointment'].search([('doctor_id', '=', doctor.id)])
                patient_ids = appts.mapped('patient_id.id')
                unique_patients = len(set(patient_ids)) if patient_ids else 0
                chart_data.append({'doctor': doctor.name or '', 'patients': unique_patients})
            # Build a simple CSS-based histogram HTML (no SVG, no external controller)
            record.doctor_patient_chart_url = ''
            record.doctor_patient_chart = record._generate_html_histogram(chart_data)

    def _generate_html_histogram(self, data):
        """Generate a simple HTML/CSS histogram (top 5) — no SVG, no controller."""
        if not data:
            return '<div style="text-align:center;padding:24px;color:#6c757d;"><h4>📊 No Data Available</h4><p>Add doctors and appointments to see the chart</p></div>'

        data_sorted = sorted(data, key=lambda x: x.get('patients', 0), reverse=True)
        top = data_sorted[:5]
        values = [d.get('patients', 0) for d in top]
        labels = [d.get('doctor', '') for d in top]
        max_v = max(values) if values else 1

        # Build HTML with simple horizontal bars
        rows = []
        for label, value in zip(labels, values):
            pct = int((value / max_v) * 100) if max_v else 0
            safe_label = xml_escape(label)
            bar_html = (
                '<div style="display:flex;align-items:center;margin:6px 0;">'
                + f'<div style="flex:0 0 160px;font-size:12px;color:#333;">{safe_label}</div>'
                + f'<div style="flex:1;background:#e9ecef;border-radius:6px;height:18px;margin-left:8px;position:relative;">'
                + f'<div title="{value}" style="width:{pct}%;background:#007bff;height:100%;border-radius:6px;"></div>'
                + f'<div style="position:absolute;right:6px;top:0;font-size:11px;color:#fff;height:18px;display:flex;align-items:center;padding-left:4px;">{value}</div>'
                + '</div>'
                + '</div>'
            )
            rows.append(bar_html)

        html = (
            '<div style="width:100%;display:block;">'
            '<div style="width:100%;background:#fff;padding:10px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">'
            '<h4 style="text-align:center;margin:4px 0 10px;color:#495057;font-weight:600;">📊 Top 5 Doctors by Patients</h4>'
            + ''.join(rows) +
            '</div></div>'
        )
        return html

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

