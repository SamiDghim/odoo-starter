from odoo import models, fields, api

# Définition du modèle "Médecin"
class MedicalDoctor(models.Model):
    _name = 'medical.doctor'               # Nom technique (table en DB : medical_doctor)
    _description = 'Médecin'               # Description lisible par l'utilisateur
    _order = 'name'                        # Ordre par défaut

    name = fields.Char(                    # Champ de type "texte"
        string="Nom du médecin",           # Libellé affiché dans Odoo
        required=True,                     # Obligatoire
        default="Dr. "                     # Valeur par défaut
    )
    
    email = fields.Char(
        string="Email",
        help="Email professionnel du médecin"
    )
    
    phone = fields.Char(
        string="Téléphone",
        help="Numéro de téléphone professionnel"
    )
    
    speciality = fields.Char(
        string="Spécialité",
        help="Spécialité médicale du docteur"
    )
    
    license_number = fields.Char(
        string="Numéro de licence",
        help="Numéro de licence professionnelle"
    )
    
    active = fields.Boolean(
        string="Actif",
        default=True,
        help="Décocher pour archiver le médecin"
    )

    patient_count = fields.Integer(        # Champ entier (stocke le nombre de patients)
        string="Nombre de patients",       
        compute="_compute_patient_count"   # Champ calculé (ne se sauvegarde pas, se calcule à la volée)
    )

    # Optional inverse relation for easier counting and fast grouping
    patient_ids = fields.One2many('medical.patient', 'doctor_id', string='Patients')
    # Link to appointments so we can depend on appointment changes
    appointment_ids = fields.One2many('medical.appointment', 'doctor_id', string='Appointments')

    @api.depends('patient_ids', 'appointment_ids.patient_id')
    def _compute_patient_count(self):      # Fonction qui calcule le nombre de patients par docteur
        # Compute number of unique patients per doctor.
        # Many setups link patients to doctors via appointments (medical.appointment.patient_id + doctor_id)
        # so counting distinct patients from appointments is a robust approach.
        if not self:
            return
        cr = self.env.cr
        ids = tuple(self.ids)
        # Prepare default counts
        counts = {doc_id: 0 for doc_id in self.ids}
        try:
            # Use SQL COUNT(DISTINCT patient_id) grouped by doctor_id for accuracy and performance
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
            # Fallback: iterate and compute using Python (slower)
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

    def action_open_patients(self):        # Action déclenchée quand on clique sur le smart button
        self.ensure_one()
        # Build a domain that matches patients with direct doctor_id OR patients who have appointments with this doctor
        Appointment = self.env['medical.appointment']
        # Find patient ids who have appointments with this doctor
        appt_patient_ids = Appointment.search([('doctor_id', '=', self.id)]).mapped('patient_id.id')
        domain = ['|', ('doctor_id', '=', self.id), ('id', 'in', appt_patient_ids or [])]
        return {
            'type': 'ir.actions.act_window',    # Type d'action → ouvre une fenêtre
            'name': f'Patients de {self.name}',      # Titre affiché en haut de la vue
            'res_model': 'medical.patient',     # Le modèle qu'on ouvre
            'view_mode': 'tree,form',           # Modes de vue : liste (tree) + formulaire (form)
            'domain': domain,
            'context': {'default_doctor_id': self.id},# Préremplir doctor_id si on crée un patient
        }