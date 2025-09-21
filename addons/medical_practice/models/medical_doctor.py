from odoo import models, fields, api


# New model for medical specialities so specialities are normalized and creatable
class MedicalSpeciality(models.Model):
    _name = 'medical.speciality'
    _description = 'Medical Speciality'

    name = fields.Char(string='Speciality', required=True)


# Définition du modèle "Médecin"
class MedicalDoctor(models.Model):
    _name = 'medical.doctor'               # Nom technique (table en DB : medical_doctor)
    _description = 'Médecin'               # Description lisible par l'utilisateur
    _order = 'name'                        # Ordre par défaut

    name = fields.Char(
        string="Nom du médecin",
        required=True,
        default="Dr. "
    )

    email = fields.Char(
        string="Email",
        help="Email professionnel du médecin"
    )

    phone = fields.Char(
        string="Téléphone",
        help="Numéro de téléphone professionnel"
    )

    # Use a Many2one to medical.speciality so specialities can be selected from the DB
    speciality_id = fields.Many2one('medical.speciality', string='Spécialité', ondelete='set null')

    # For convenience, keep a computed / stored char field mirroring the name (optional)
    speciality_name = fields.Char(related='speciality_id.name', string='Spécialité (texte)', readonly=True)

    license_number = fields.Char(
        string="Numéro de licence",
        help="Numéro de licence professionnelle"
    )

    active = fields.Boolean(
        string="Actif",
        default=True,
        help="Décocher pour archiver le médecin"
    )

    patient_count = fields.Integer(
        string="Nombre de patients",
        compute="_compute_patient_count"
    )

    # Optional inverse relation for easier counting and fast grouping
    patient_ids = fields.One2many('medical.patient', 'doctor_id', string='Patients')
    # Link to appointments so we can depend on appointment changes
    appointment_ids = fields.One2many('medical.appointment', 'doctor_id', string='Appointments')

    @api.depends('patient_ids', 'appointment_ids.patient_id')
    def _compute_patient_count(self):
        if not self:
            return
        cr = self.env.cr
        ids = tuple(self.ids)
        counts = {doc_id: 0 for doc_id in self.ids}
        try:
            query = f"""
                SELECT doctor_id, COUNT(DISTINCT patient_id) AS c
                FROM medical_appointment
                WHERE doctor_id IN %s AND patient_id IS NOT NULL
                GROUP BY doctor_id
            """
            cr.execute(query, (ids,))
            for row in cr.fetchall():
                doc_id, c = row
                counts[doc_id] = c or 0
        except Exception:
            Appointment = self.env['medical.appointment']
            for doctor in self:
                try:
                    appts = Appointment.search([('doctor_id', '=', doctor.id)])
                    patient_ids = appts.mapped('patient_id.id')
                    doctor.patient_count = len(set([p for p in patient_ids if p]))
                except Exception:
                    doctor.patient_count = 0
            return

        for doctor in self:
            doctor.patient_count = counts.get(doctor.id, 0)

    def action_open_patients(self):
        self.ensure_one()
        Appointment = self.env['medical.appointment']
        appt_patient_ids = Appointment.search([('doctor_id', '=', self.id)]).mapped('patient_id.id')
        domain = ['|', ('doctor_id', '=', self.id), ('id', 'in', appt_patient_ids or [])]
        return {
            'type': 'ir.actions.act_window',
            'name': f'Patients de {self.name}',
            'res_model': 'medical.patient',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_doctor_id': self.id},
        }