from odoo import models, fields, api

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

    @api.depends()
    def _compute_counts(self):
        for record in self:
            # Patient counts
            record.patient_count = self.env['medical.patient'].search_count([])
            
            # Doctor counts
            record.doctor_count = self.env['medical.doctor'].search_count([])
            
            # Appointment counts
            record.appointment_count = self.env['medical.appointment'].search_count([])
            
            # Prescription counts
            record.prescriptions_count = self.env['medical.prescription'].search_count([])

    @api.depends()
    def _compute_doctor_patient_chart(self):
        for record in self:
            # Get all doctors and their patient counts
            doctors = self.env['medical.doctor'].search([])
            chart_data = []
            
            for doctor in doctors:
                # Count unique patients assigned to this doctor through appointments
                appointments = self.env['medical.appointment'].search([
                    ('doctor_id', '=', doctor.id)
                ])
                
                # Get unique patient IDs from appointments
                patient_ids = appointments.mapped('patient_id.id')
                unique_patients = len(set(patient_ids)) if patient_ids else 0
                
                chart_data.append({
                    'doctor': doctor.name,
                    'patients': unique_patients
                })
            
            # Generate HTML chart
            record.doctor_patient_chart = record._generate_chart_html(chart_data)

    def _generate_chart_html(self, data):
        """Generate HTML with Bar Chart for doctor-patient visualization"""
        if not data:
            return '''
            <div style="text-align: center; padding: 50px; color: #6c757d; background-color: #f8f9fa; border-radius: 8px;">
                <h4 style="color: #6c757d;">📊 No Data Available</h4>
                <p>Add doctors and appointments to see the chart</p>
                <small>Create doctors and assign them to appointments to visualize the doctor-patient relationship</small>
            </div>
            '''
        
        # Create a simple bar chart representation
        max_patients = max([item['patients'] for item in data]) if data else 1
        if max_patients == 0:
            max_patients = 1
        
        html_content = '''
        <div style="width: 100%; height: 400px; padding: 20px;">
            <h4 style="text-align: center; margin-bottom: 30px; color: #495057;">📊 Patients per Doctor</h4>
            <div style="display: flex; align-items: end; justify-content: space-around; height: 300px; border-bottom: 2px solid #333; border-left: 2px solid #333; padding: 10px;">
        '''
        
        for item in data:
            doctor_name = item['doctor']
            patient_count = item['patients']
            # Calculate bar height (max 250px)
            bar_height = int((patient_count / max_patients) * 250) if max_patients > 0 else 0
            
            html_content += f'''
                <div style="display: flex; flex-direction: column; align-items: center; margin: 0 10px;">
                    <div style="background-color: #007cba; width: 60px; height: {bar_height}px; border-radius: 4px 4px 0 0; position: relative; display: flex; align-items: end; justify-content: center;">
                        <span style="color: white; font-weight: bold; font-size: 12px; margin-bottom: 5px;">{patient_count}</span>
                    </div>
                    <div style="margin-top: 10px; text-align: center; font-size: 12px; color: #333; max-width: 80px; word-wrap: break-word;">
                        {doctor_name}
                    </div>
                </div>
            '''
        
        html_content += '''
            </div>
            <div style="text-align: center; margin-top: 20px; color: #6c757d; font-size: 14px;">
                <p><strong>Blue bars represent the number of patients per doctor</strong></p>
            </div>
        </div>
        '''
        
        return html_content

    def action_open_patients(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'All Patients',
            'res_model': 'medical.patient',
            'view_mode': 'tree,form',
            'domain': [],
        }

    def action_open_doctors(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'All Doctors',
            'res_model': 'medical.doctor',
            'view_mode': 'tree,form',
            'domain': [],
        }

    def action_open_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'All Appointments',
            'res_model': 'medical.appointment',
            'view_mode': 'calendar,tree,form',
            'domain': [],
        }

    def action_open_prescriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'All Prescriptions',
            'res_model': 'medical.prescription',
            'view_mode': 'tree,form',
        }
