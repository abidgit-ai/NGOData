from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.exc import OperationalError

app = Flask(__name__)
engine = create_engine('sqlite:///forms.db', echo=True)
metadata = MetaData()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_form', methods=['GET', 'POST'])
def create_form():
    if request.method == 'POST':
        form_name = request.form['form_name']
        fields = request.form['fields'].split(',')
        columns = [Column('id', Integer, primary_key=True)]
        for f in fields:
            clean = f.strip().lower().replace(' ', '_')
            columns.append(Column(clean, String))
        try:
            Table(form_name, metadata, *columns)
            metadata.create_all(engine)
        except OperationalError as e:
            return f"Error creating table: {e}"
        return redirect(url_for('index'))
    return render_template('create_form.html')

if __name__ == '__main__':
    metadata.create_all(engine)
    app.run(debug=True)
