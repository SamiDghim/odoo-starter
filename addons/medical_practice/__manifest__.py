{
    'name': 'Medical Practice Management',
    'version': '1.0.0',
    'category': 'Healthcare',
    'summary': 'Complete medical practice management system',
    'description': """
        Medical Practice Management System
        ==================================
        
        Features:
        * Patient management with medical history
        * Appointment scheduling and tracking
        * Medical records and visit documentation
        * Prescription management
        * User-friendly interface
    """,
    'depends': ['base', 'mail', 'calendar', 'web'],
    'data': [
        # Security
        'security/medical_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/sequences.xml',
        
        # Views
        'views/patient_views.xml',
        'views/appointment_views.xml',
        'views/medical_record_views.xml',
        'views/prescription_views.xml',
        'views/medical_dashboard_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}