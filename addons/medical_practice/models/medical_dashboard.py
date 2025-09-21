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

    # Chart Field
    doctor_patient_chart = fields.Html(string="Doctor-Patient Chart", compute="_compute_doctor_patient_chart")
    doctor_patient_chart_url = fields.Char(string='Doctor Patient Chart URL', compute='_compute_doctor_patient_chart')
    dashboard_charts = fields.Html(string='Dashboard Charts', compute='_compute_dashboard_charts')

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

    @api.depends()
    def _compute_dashboard_charts(self):
        """Compute a 2x2 grid of charts:
        - Patients / Doctors (horizontal bars per doctor)
        - Patients / Date (weekly)
        - Prescriptions / Doctors (horizontal bars per doctor)
        - Prescriptions / Date (monthly)
        """
        for record in self:
            # Patients per doctor
            doctors = self.env['medical.doctor'].search([('active', '=', True)])
            patients_per_doctor = []
            for doctor in doctors:
                appts = self.env['medical.appointment'].search([('doctor_id', '=', doctor.id)])
                patient_ids = appts.mapped('patient_id.id')
                unique_patients = len(set(patient_ids)) if patient_ids else 0
                patients_per_doctor.append({'doctor': doctor.name or '', 'patients': unique_patients})

            # Prescriptions per doctor
            prescriptions_per_doctor = []
            for doctor in doctors:
                pres = self.env['medical.prescription'].search([('doctor_id', '=', doctor.id)])
                prescriptions_per_doctor.append({'doctor': doctor.name or '', 'prescriptions': len(pres)})

            # Patients per date (weekly aggregation over last 12 weeks)
            patients_by_week = self._aggregate_model_counts_by_period('medical.patient', 'create_date', 'week', periods=12)

            # Prescriptions per date (monthly aggregation over last 12 months)
            prescriptions_by_month = self._aggregate_model_counts_by_period('medical.prescription', 'prescription_date', 'month', periods=12)

            # Build HTML panels
            panel1 = record._generate_html_histogram([{'doctor': d['doctor'], 'patients': d['patients']} for d in patients_per_doctor], title='Patients per Doctor')
            panel2 = record._generate_html_timeseries(patients_by_week, title='Patients per Week')
            panel3 = record._generate_html_histogram([{'doctor': d['doctor'], 'patients': d['prescriptions']} for d in prescriptions_per_doctor], title='Prescriptions per Doctor')
            panel4 = record._generate_html_timeseries(prescriptions_by_month, title='Prescriptions per Month')

            # Compose 2x2 grid
            grid = (
                '<div style="display:flex;flex-wrap:wrap;gap:16px;">'
                + f'<div style="flex:1 1 48%;min-width:320px;">{panel1}</div>'
                + f'<div style="flex:1 1 48%;min-width:320px;">{panel2}</div>'
                + f'<div style="flex:1 1 48%;min-width:320px;">{panel3}</div>'
                + f'<div style="flex:1 1 48%;min-width:320px;">{panel4}</div>'
                + '</div>'
            )
            # Add pie chart for Patients by Blood Type below the grid
            blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            counts = []
            for bt in blood_types:
                c = self.env['medical.patient'].search_count([('blood_type', '=', bt)])
                counts.append({'label': bt, 'count': c})

            pie = record._generate_pie_chart(counts, title='Patients by Blood Type')

            record.dashboard_charts = grid + '<div style="margin-top:16px;">' + pie + '</div>'

    def _generate_pie_chart(self, data, title=None):
        """Generate a CSS conic-gradient based pie chart (camembert) and a legend.
        `data` is list of {'label','count'}.
        """
        total = sum(d.get('count', 0) for d in data)
        if total == 0:
            return '<div style="text-align:center;padding:18px;color:#6c757d;"><h4>No Data</h4><p>No patients with recorded blood types</p></div>'

        # Colors for slices
        colors = ['#007bff', '#6610f2', '#6f42c1', '#e83e8c', '#fd7e14', '#ffc107', '#28a745', '#20c997']

        # Build SVG pie slices
        cx = 110
        cy = 110
        r = 100
        angle_offset = -90  # start at top
        current_angle = angle_offset
        svg_slices = []
        legend_items = []
        bars = []

        for i, d in enumerate(data):
            val = d.get('count', 0)
            if val <= 0:
                continue
            pct = val / total
            sweep = pct * 360
            start_angle = current_angle
            end_angle = current_angle + sweep

            def _polar_to_cartesian(cx, cy, r, angle_deg):
                rad = math.radians(angle_deg)
                return cx + r * math.cos(rad), cy + r * math.sin(rad)

            start_x, start_y = _polar_to_cartesian(cx, cy, r, start_angle)
            end_x, end_y = _polar_to_cartesian(cx, cy, r, end_angle)
            large_arc = 1 if sweep > 180 else 0
            color = colors[i % len(colors)]
            path_d = f'M {cx} {cy} L {start_x:.4f} {start_y:.4f} A {r} {r} 0 {large_arc} 1 {end_x:.4f} {end_y:.4f} Z'
            svg_slices.append(f'<path d="{path_d}" fill="{color}" stroke="#fff" stroke-width="1"/>')

            legend_items.append(f"<div style='display:flex;align-items:center;margin:4px 0;'><div style='width:12px;height:12px;background:{color};border-radius:2px;margin-right:8px;'></div><div style='font-size:12px;color:#333'>{xml_escape(d.get('label'))} — {val}</div></div>")

            # horizontal bar fallback
            bar_width_pct = int(pct * 100)
            bars.append(f"<div style='margin:6px 0;'><div style='font-size:12px;color:#333;margin-bottom:4px;'>{xml_escape(d.get('label'))} — {val}</div><div style='background:#e9ecef;border-radius:6px;height:14px;overflow:hidden'><div style='width:{bar_width_pct}%;background:{color};height:100%'></div></div></div>")

            current_angle = end_angle

        svg = (
            f'<svg width="220" height="220" viewBox="0 0 220 220" xmlns="http://www.w3.org/2000/svg">'
            + ''.join(svg_slices)
            + '</svg>'
        )

        pie_html = (
            '<div style="display:flex;gap:18px;align-items:flex-start;flex-wrap:wrap;">'
            + f'<div>{svg}</div>'
            + f'<div style="min-width:160px;">{''.join(legend_items)}</div>'
            + f'<div style="flex-basis:100%;margin-top:12px">{''.join(bars)}</div>'
            + '</div>'
        )

        if title:
            pie_html = f'<div style="background:#fff;padding:10px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.06);"><div style="font-weight:600;margin-bottom:8px;font-size:13px;color:#333;">{xml_escape(title)}</div>' + pie_html + '</div>'

        return pie_html

    def _aggregate_model_counts_by_period(self, model_name, date_field, period='week', periods=12):
        """Return list of {'period': label, 'count': n} tuples for the last `periods` periods.
        period: 'week' or 'month'. Uses server-side date arithmetic and ORM searches.
        """
        Model = self.env[model_name]
        # Determine ranges
        from datetime import datetime, timedelta
        now = fields.Date.context_today(self)
        buckets = []
        results = []

        if period == 'week':
            # Last `periods` weeks (starting on Monday)
            start_date = now - timedelta(weeks=periods)
            for i in range(periods, 0, -1):
                end = now - timedelta(weeks=i-1)
                start = end - timedelta(weeks=1)
                label = start.strftime('%Y-%m-%d') + ' to ' + (end - timedelta(days=1)).strftime('%Y-%m-%d')
                buckets.append((start, end, label))
        else:
            # months (avoid external dependencies like python-dateutil)
            from datetime import date as _date

            def _month_subtract(d, months):
                year = d.year
                month = d.month - months
                while month <= 0:
                    month += 12
                    year -= 1
                return _date(year, month, 1)

            ref = now if isinstance(now, _date) else _date.fromisoformat(str(now))
            ref_month_start = _date(ref.year, ref.month, 1)
            for i in range(periods, 0, -1):
                start = _month_subtract(ref_month_start, i)
                end = _month_subtract(ref_month_start, i-1)
                label = start.strftime('%Y-%m')
                buckets.append((start, end, label))

        for start, end, label in buckets:
            domain = [(date_field, '>=', start.strftime('%Y-%m-%d')), (date_field, '<', end.strftime('%Y-%m-%d'))]
            count = Model.search_count(domain)
            results.append({'period': label, 'count': count})

        return results

    def _generate_html_timeseries(self, series, title='Timeseries'):
        """Generate a compact bar/line-like timeseries using simple divs. series is list of {'period','count'}"""
        if not series:
            return '<div style="text-align:center;padding:24px;color:#6c757d;"><h4>No Data</h4></div>'
        values = [s['count'] for s in series]
        labels = [s['period'] for s in series]
        max_v = max(values) if values else 1

        bars = []
        for lab, val in zip(labels, values):
            pct = int((val / max_v) * 100) if max_v else 0
            safe_label = xml_escape(str(lab))
            bars.append(
                f'<div style="display:inline-block;width:calc(100%/{len(values)} - 4px);margin:2px;vertical-align:bottom;">'
                + f'<div title="{val}" style="height:{max(6,pct)}px;background:#17a2b8;border-radius:4px;margin-bottom:6px;"></div>'
                + f'<div style="font-size:10px;color:#666;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{safe_label}</div>'
                + '</div>'
            )

        html = (
            '<div style="background:#fff;padding:10px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">'
            + f'<div style="font-weight:600;margin-bottom:8px;font-size:13px;color:#333;">{xml_escape(title)}</div>'
            + '<div style="display:flex;align-items:flex-end;height:120px;">'
            + ''.join(bars)
            + '</div></div>'
        )
        return html

    def _generate_html_histogram(self, data, title=None):
        """Generate a simple HTML/CSS histogram for all doctors (no SVG, no controller).
        Optional `title` will be rendered above the histogram panel.
        """
        if not data:
            return '<div style="text-align:center;padding:24px;color:#6c757d;"><h4>📊 No Data Available</h4><p>Add doctors and appointments to see the chart</p></div>'

        # Sort all doctors by patients descending but include everyone
        data_sorted = sorted(data, key=lambda x: x.get('patients', 0), reverse=True)
        values = [d.get('patients', 0) for d in data_sorted]
        labels = [d.get('doctor', '') for d in data_sorted]
        max_v = max(values) if values else 1

        # Build HTML with simple horizontal bars for all doctors
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

        # Optional title
        title_html = ''
        if title:
            title_html = f'<div style="font-weight:600;margin-bottom:8px;font-size:13px;color:#333;">{xml_escape(title)}</div>'

        html = (
            '<div style="width:100%;display:block;">'
            + f'<div style="width:100%;background:#fff;padding:10px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">'
            + title_html
            + ''.join(rows)
            + '</div></div>'
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

