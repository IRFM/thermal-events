from sqlalchemy.ext.declarative import declarative_base


def keyvalgen(obj):
    """Generate attribute name/value pairs, filtering out SQLAlchemy attributes.

    Args:
        obj: The object to generate attribute name/value pairs from.

    Yields:
        Tuple[str, Any]: The attribute name/value pairs.

    """
    excl = ("_sa_adapter", "_sa_instance_state")
    for k, v in vars(obj).items():
        if not k.startswith("_") and not any(hasattr(v, a) for a in excl):
            yield k, v


class CustomBase:
    """Custom base class for SQLAlchemy declarative models."""

    def __repr__(self):
        """Return a string representation of the object.

        Returns:
            str: The string representation of the object.

        """
        params = ", ".join(f"{k}={v}" for k, v in keyvalgen(self))
        return f"{self.__class__.__name__}({params})"


Base = declarative_base(cls=CustomBase)
