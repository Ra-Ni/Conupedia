import mysql.connector

def session():
    retval = mysql.connector.connect(
        host="localhost",
        user="yourusername",
        password="yourpassword"
    )

    print(retval)
    return retval


if __name__ == '__main__':
    s = session()
