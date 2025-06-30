from flask import Flask, render_template, request, redirect, url_for

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

app = Flask(__name__)
engine = create_engine('sqlite:///forms.db', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()
metadata = MetaData()

class Survey(Base):
    __tablename__ = 'surveys'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey('surveys.id'))
    parent_id = Column(Integer, ForeignKey('questions.id'), nullable=True)
    slug = Column(String, nullable=False)
    label = Column(String, nullable=False)
    qtype = Column(String, nullable=False)
    required = Column(Boolean, default=False)
    order = Column(Integer, default=0)

    survey = relationship('Survey', backref='questions')

Base.metadata.create_all(engine)

@app.route('/')
def index():
    session = Session()
    surveys = session.query(Survey).all()
    return render_template('index.html', surveys=surveys)

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

@app.route('/create_survey', methods=['GET', 'POST'])
def create_survey():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        session = Session()
        survey = Survey(title=title, description=description)
        session.add(survey)
        session.commit()
        return redirect(url_for('add_question', survey_id=survey.id))
    return render_template('create_survey.html')

@app.route('/survey/<int:survey_id>/questions', methods=['GET', 'POST'])
def add_question(survey_id):
    session = Session()
    survey = session.get(Survey, survey_id)
    groups = [q for q in survey.questions if q.qtype == 'group']
    if request.method == 'POST':
        slug = request.form['slug']
        label = request.form['label']
        qtype = request.form['qtype']
        parent_id = request.form.get('parent_id')
        parent_id = int(parent_id) if parent_id else None
        required = bool(request.form.get('required'))
        order = int(request.form.get('order', 0))
        q = Question(survey_id=survey.id, slug=slug, label=label,
                     qtype=qtype, required=required, order=order,
                     parent_id=parent_id)
        session.add(q)
        session.commit()
        return redirect(url_for('add_question', survey_id=survey.id))
    questions = session.query(Question).filter_by(survey_id=survey.id).order_by(Question.order).all()
    return render_template('add_question.html', survey=survey, questions=questions, groups=groups)


def generate_response_tables(survey_id):
    session = Session()
    questions = session.query(Question).filter_by(survey_id=survey_id).order_by(Question.order).all()
    meta = MetaData(bind=engine)

    main_cols = [Column('id', Integer, primary_key=True)]
    groups = []
    for q in questions:
        if q.qtype == 'group':
            groups.append(q)
        elif q.parent_id is None:
            main_cols.append(Column(q.slug, String))
    Table(f'responses_survey_{survey_id}', meta, *main_cols, extend_existing=True)
    meta.create_all()

    for g in groups:
        cols = [Column('id', Integer, primary_key=True),
                Column('response_id', Integer, ForeignKey(f'responses_survey_{survey_id}.id'))]
        children = [c for c in questions if c.parent_id == g.id]
        for c in children:
            cols.append(Column(c.slug, String))
        Table(f'responses_survey_{survey_id}_subform_{g.id}', meta, *cols, extend_existing=True)
    meta.create_all()

@app.route('/survey/<int:survey_id>/generate', methods=['POST'])
def generate(survey_id):
    generate_response_tables(survey_id)
    return redirect(url_for('survey', survey_id=survey_id))

@app.route('/survey/<int:survey_id>', methods=['GET', 'POST'])
def survey(survey_id):
    session = Session()
    survey = session.get(Survey, survey_id)
    questions = session.query(Question).filter_by(survey_id=survey_id).order_by(Question.order).all()
    groups = [q for q in questions if q.qtype == 'group']
    root_questions = [q for q in questions if q.parent_id is None and q.qtype != 'group']
    children_map = {}
    for q in questions:
        if q.parent_id:
            children_map.setdefault(q.parent_id, []).append(q)
    if request.method == 'POST':
        meta = MetaData(bind=engine)
        main_table = Table(f'responses_survey_{survey_id}', meta, autoload_with=engine)
        conn = engine.connect()
        main_values = {q.slug: request.form.get(q.slug) for q in root_questions}
        result = conn.execute(main_table.insert().values(**main_values))
        response_id = result.inserted_primary_key[0]
        for g in groups:
            table = Table(f'responses_survey_{survey_id}_subform_{g.id}', meta, autoload_with=engine)
            index = 0
            while True:
                prefix = f'g{g.id}_{index}_'
                if not any(key.startswith(prefix) for key in request.form.keys()):
                    break
                row = {c.slug: request.form.get(prefix + c.slug) for c in children_map.get(g.id, [])}
                row['response_id'] = response_id
                conn.execute(table.insert().values(**row))
                index += 1
        conn.close()
        return redirect(url_for('index'))
    return render_template(
        'survey.html',
        survey=survey,
        root_questions=root_questions,
        groups=groups,
        children_map=children_map,
    )

if __name__ == '__main__':
    metadata.create_all(engine)
    app.run(debug=True)
