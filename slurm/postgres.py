from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.engine.url import URL
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import exc
from sqlalchemy.dialects.postgresql import ARRAY
from contextlib import contextmanager
from sqlalchemy.sql import select

Base = declarative_base()

class ToolTypeMixin(object):
    """ Gather information about processing status """

    id = Column(Integer, primary_key=True)
    case_id = Column(String)
    vcf_id = Column(String)
    files = Column(ARRAY(String))
    status = Column(String)
    location = Column(String)

    def __repr__(self):
        return "<ToolTypeMixin(case_id='%s', status='%s' , location='%s'>" %(self.case_id,
                self.status, self.location)

class Somaticsniper(ToolTypeMixin, Base):

    __tablename__ = 'somaticsniper_table'


def db_connect(database):
    """performs database connection"""

    return create_engine(URL(**database))

def create_table(engine, tool):
    """ checks if a table  exists and create one if it doesn't """

    inspector = Inspector.from_engine(engine)
    tables = set(inspector.get_table_names())
    if tool.__tablename__ not in tables:
        Base.metadata.create_all(engine)

class Status(object):
    pass

class Files(object):
    pass

def add_status(engine, case_id, vcf_id, file_ids, status, output_location):
    """ add provided metrics to database """

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    met = Somaticsniper(case_id = case_id,
                    vcf_id = vcf_id,
                    files=file_ids,
                    status=status,
                    location=output_location)

    create_table(engine, met)

    session.add(met)
    session.commit()
    session.close()

def get_complete_cases(engine):
    """ Get complete cases from the database """

    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()

    meta = MetaData(engine)

    #read the coclean table
    status = Table('coclean_caseid_gdcid', meta,
                        Column("case_id", String, primary_key=True),
                        Column("gdc_id", String, primary_key=True),
                        autoload=True)

    mapper(Status, status)

    #read harmonized files table
    data = Table('harmonized_files', meta,
                    Column("case_id", String, primary_key=True),
                    Column("gdc_id", String, primary_key=True),
                    Column("docker_tag", String, primary_key=True),
                    autoload=True)
    mapper(Files, data)

    #check for complete cases
    complete_cases = session.query(Status).filter(Status.status == 'COMPLETE').all()


    tumor = dict()
    tumor_file = dict()
    normal = dict()
    normal_file = dict()

    for row in complete_cases:
        data_details = session.query(Files).filter(Files.gdc_id == row.gdc_id).first()
        sample_type = data_details.sample_type
        case_id = str(row.case_id)
        gdc_id = str(row.gdc_id)
        output_location = str(row.output_location)

        if "tumor" in sample_type.lower():
            if case_id not in tumor:
                tumor[case_id] = list()
                tumor_file[case_id] = list()

            tumor[case_id].append(gdc_id)
            tumor_file[case_id].append(output_location)

        if "normal" in sample_type.lower():
            if case_id not in normal:
                normal[case_id] = list()
                normal_file[case_id] = list()

            normal[case_id].append(gdc_id)
            normal_file[case_id].append(output_location)


    session.close()
    return(tumor, tumor_file, normal, normal_file)
