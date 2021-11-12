import core


def users():
    session = core.session()
    query = """
    select ?user where {
        ?user a 
    }
    """
    session.post()