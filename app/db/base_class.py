from sqlalchemy.ext.declarative import as_declarative, declared_attr

# Base class for SQLAlchemy models, using the declarative system. This allows us to define our models as classes.
@as_declarative()
class Base:
    id: any
    __name__: str
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()