import sshtunnel, keys, config
from sqlalchemy import create_engine, String, Column, Identity, BigInteger, ForeignKey, desc
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

sshtunnel.SSH_TIMEOUT = 200.0
sshtunnel.TUNNEL_TIMEOUT = 200.0

base = declarative_base()

class Metric(base):
    __tablename__ = "metric"
    id = Column(BigInteger, Identity(),primary_key=True)
    name = Column(String)
    unit = Column(String)
    chart = Column(String)
    key = Column(String)
    type = Column(String)
    format = Column(String)
    project_slug = Column(String)
    project = Column(String)

    def __init__(self, name, unit, chart, key, type, format, project_slug, project):
        self.name = name
        self.unit = unit
        self.chart = chart
        self.key = key
        self.type = type
        self.format = format
        self.project_slug = project_slug
        self.project = project

class CompanyImpactData(base):
    __tablename__ = "company_impact_data"
    id = Column(BigInteger, Identity(), primary_key=True)
    metric_id = Column(BigInteger, ForeignKey('metric.id'))
    value = Column(String)
    date = Column(String)
    note = Column(String)

    metric = relationship('Metric', back_populates='company_impact_data', lazy='subquery')

    def __init__(self, metric_id, value, date, note):
        self.metric_id = metric_id
        self.value = value
        self.date = date
        self.note = note

Metric.company_impact_data = relationship("CompanyImpactData", order_by = desc(CompanyImpactData.date), back_populates="metric", lazy="subquery")

# SSH tunnel

def sshTunnel():
    tunnel = sshtunnel.SSHTunnelForwarder(
        (config.SSH_HOST, config.SSH_PORT),
        ssh_username=config.SSH_USER,
        ssh_password=keys.MYSQL_SSH_KEY,
        remote_bind_address=(config.MYSQL_DB_HOST, int(config.MYSQL_DB_PORT))
    )

    return tunnel

# MySQL db initiation

def createEngine(local_port):
    engine = create_engine('mysql://' + config.SSH_USER + ':' + keys.MYSQL_DB_KEY + '@127.0.0.1:' + local_port + '/' + config.MYSQL_DB_NAME, connect_args={'connect_timeout': 200}, pool_size=10, max_overflow=20)
    factory = sessionmaker(bind=engine)
    session = factory()

    return session

def addImpactData(object):

    with sshTunnel() as server:
        local_port = str(server.local_bind_port)  
        session = createEngine(local_port)

        session.add_all(object)
        session.commit()

    return "Success"

def getDashboardData():
    with sshTunnel() as server:
        local_port = str(server.local_bind_port)  
        session = createEngine(local_port)

        data = session.query(CompanyImpactData).join(Metric).filter(Metric.key != None).order_by(desc(CompanyImpactData.date)).all()
        session.close()
    return data

def getProjectImpactData(slug):
    with sshTunnel() as server:
        local_port = str(server.local_bind_port)  
        session = createEngine(local_port)

        data = session.query(CompanyImpactData).join(Metric).filter(Metric.project_slug == slug).order_by(desc(CompanyImpactData.date)).all()
        session.close()
    return data