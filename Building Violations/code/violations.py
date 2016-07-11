# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Imports - for Flask Application & Dependencies                #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
from flask import render_template, url_for, flash, redirect, request, Markup
from app import app, db
import requests
from .modals import violations_csv_upload_modal
from .includes import csv2json_conversion, Import_Data, validate_columns, validate_import, add_to_db, get_upload_columns


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# CSV Upload Logic							                    #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
@app.route('/upload', methods=['POST'])
def upload():
    f = request.files['data_file'].read().decode('utf-8')

    if not f:
        flash("Error. File upload attempt detected, but no file found. Please contact the application administrator.",
              'danger')

    if True:
        f = csv2json_conversion(f)
        import_data = Import_Data(f)
        data_context = request.form['form_submit']
        valid_schema = validate_columns(import_data, data_context)
        if valid_schema == True:
            validated_data = validate_import(current_user, import_data, data_context)
            if validated_data:
                add_to_db(validated_data, data_context)
    else:
        flash('Error. Incorrect file type. The only file types accepted are: .csv', 'danger')

    return redirect(request.referrer)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Model - Not necessary, but wanted persistence.                #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class Violations(db.Model):
    __tablename__ = 'violations'

    db_columns = {
        'violation_id': {'required': True, 'validators': 'integer', 'validator_parameters': {}},
        'inspection_id': {'required': False, 'validators': 'integer', 'validator_parameters': {}},
        'violation_category': {'required': False, 'validators': 'string', 'validator_parameters': {'max': 100}},
        'violation_date': {'required': False, 'validators': 'string', 'validator_parameters': {'max': 100}},
        'violation_date_closed': {'required': False, 'validators': 'string', 'validator_parameters': {'max': 100}},
        'violation_type': {'required': False, 'validators': 'string', 'validator_parameters': {'max': 100}},
    }

    violation_id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, index=True)
    violation_category = db.Column(db.String(100), index=True)
    violation_date = db.Column(db.String(100), index=True)
    violation_date_closed = db.Column(db.String(100), index=True)
    violation_type = db.Column(db.String(100), index=True)

    created_on = db.Column(db.DateTime, default=db.func.now(), index=True)
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), index=True)

    def __init__(self, violation_id, inspection_id, violation_category, violation_date, violation_date_closed,violation_type):
        self.violation_id = violation_id
        self.inspection_id = inspection_id
        self.violation_category = violation_category
        self.violation_date = violation_date
        self.violation_date_closed = violation_date_closed
        self.violation_type = violation_type

    def __repr__(self):
        return '<id: {}>'.format(self.violation_id)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Logic                                                         #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
@app.route('/violations')
def violations():
    import datetime
    logged_in = current_user.is_authenticated()
    login_form = LoginForm(request.form)
    modular_cdn_scripts = ('//cdnjs.cloudflare.com/ajax/libs/Chart.js/2.1.4/Chart.bundle.min.js',)

    violations_data = db.session.query(Violations)

    categories = []
    category_data = {}

    for row in violations_data:
        if row.violation_category not in categories:
            categories.append(row.violation_category)

    for category in categories:
        category_data[category] = {
            'total_violations': 0,
            'earliest_violation': '',
            'latest_violation': ''
        }

    for category in categories:
        for row in violations_data:
            if row.violation_category == category:
                # Get total violations.
                category_data[category]['total_violations'] += 1

                # Get earliest violation.
                if category_data[category]['earliest_violation'] == '':
                    category_data[category]['earliest_violation'] = datetime.datetime.strptime(row.violation_date,
                                                                                               '%Y-%m-%d %H:%M:%S')
                else:
                    if datetime.datetime.strptime(row.violation_date,
                                                  '%Y-%m-%d %H:%M:%S')< category_data[category]['earliest_violation']:
                        category_data[category]['earliest_violation'] = datetime.datetime.strptime(row.violation_date,
                                                                                                   '%Y-%m-%d %H:%M:%S')

                # Get latest violation.
                if category_data[category]['latest_violation'] == '':
                    category_data[category]['latest_violation'] = datetime.datetime.strptime(row.violation_date,
                                                                                               '%Y-%m-%d %H:%M:%S')
                else:
                    if datetime.datetime.strptime(row.violation_date,
                                                  '%Y-%m-%d %H:%M:%S') > category_data[category]['latest_violation']:
                        category_data[category]['latest_violation'] = datetime.datetime.strptime(row.violation_date,
                                                                                                   '%Y-%m-%d %H:%M:%S')
    from collections import OrderedDict
    category_data = OrderedDict(sorted(category_data.items()))

    return render_template('modules/analytics/violations.html',
                           icon="fa fa-dashboard",
                           module_abbreviation="Dashboard",
                           module_name='Dashboard',
                           page_name="Cool Building Violations Analytics",
                           app_config_settings=get_app_settings(),
                           messages=db.session.query(Messages),
                           notifications=db.session.query(AppNotifications),
                           login_form=login_form,
                           current_user=current_user,
                           logged_in=logged_in,
                           modular_cdn_scripts=modular_cdn_scripts,
                           csv_upload_modal=violations_csv_upload_modal,
                           upload_columns=get_upload_columns(Violations),
                           violations_data=violations_data,
                           categories=categories,
                           category_data=category_data)
