from odoo import http
from odoo.http import request


class MedicalPracticeController(http.Controller):
    @http.route('/medical_practice/doctor/<int:doctor_id>/patients', type='http', auth='user')
    def doctor_patients(self, doctor_id, **kw):
        # Build the domain fragment expected by the web client. It should be URL-encoded,
        # but the web client accepts a simple fragment like domain=[('doctor_id','=',6)]
        domain = f"[('doctor_id','=',{doctor_id})]"
        # Redirect to patient list with the domain applied in the fragment
        return request.redirect(f"/web#model=medical.patient&view_type=list&menu_id=&action=&domain={domain}")
