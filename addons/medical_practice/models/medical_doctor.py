    from odoo import models, fields

# Définition du modèle "Médecin"
class MedicalDoctor(models.Model):
    _name = 'medical.doctor'               # Nom technique (table en DB : medical_doctor)
    _description = 'Médecin'               # Description lisible par l’utilisateur

    name = fields.Char(                    # Champ de type "texte"
        string="Nom du médecin",           # Libellé affiché dans Odoo
        required=True                      # Obligatoire
    )

    patient_count = fields.Integer(        # Champ entier (stocke le nombre de patients)
        string="Nombre de patients",       
        compute="_compute_patient_count"   # Champ calculé (ne se sauvegarde pas, se calcule à la volée)
    )

    def _compute_patient_count(self):      # Fonction qui calcule le nombre de patients par docteur
        for doctor in self:                # Pour chaque docteur dans l’enregistrement
            doctor.patient_count = self.env['medical.patient'].search_count([
                ('doctor_id', '=', doctor.id)  # Chercher tous les patients dont le doctor_id correspond
            ])

    def action_open_patients(self):        # Action déclenchée quand on clique sur le smart button
        return {
            'type': 'ir.actions.act_window',    # Type d’action → ouvre une fenêtre
            'name': 'Patients du médecin',      # Titre affiché en haut de la vue
            'res_model': 'medical.patient',     # Le modèle qu’on ouvre
            'view_mode': 'tree,form',           # Modes de vue : liste (tree) + formulaire (form)
            'domain': [('doctor_id', '=', self.id)],  # Filtre → uniquement les patients liés à ce médecin
            'context': {'default_doctor_id': self.id},# Préremplir doctor_id si on crée un patient
        }
