'''Database settings
Created on Sep 2, 2010

@author: Peyman Kazemian
'''
DATABASE_ENGINE = 'django.db.backends.mysql'
'''It is possible to use sqlite, but for many of the tests to pass, we
need a database that allows concurrent accesses such as MySQL. See Django's
documentation for more information on this setting.

Options are 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.

'''

#DATABASE_NAME = "om"
'''Name of the database to use or path to database file if using sqlite3..'''

#DATABASE_USER = 'om'
'''Database username. Not used with sqlite3.'''

#DATABASE_PASSWORD = 'om'
'''Database username password. Not used with sqlite3.'''

#DATABASE_HOST = ''
'''Set to empty string for localhost. Not used with sqlite3.'''

#DATABASE_PORT = ''
'''Set to empty string for default. Not used with sqlite3.'''

DATABASE_PORT = ''
DATABASE_NAME = "optin"
DATABASE_USER = "userName"
DATABASE_PASSWORD = "password"
DATABASE_HOST = "127.0.0.1"
DATABASE_ENGINE = "django.db.backends.mysql"
DATABASES = { 'default': {'ENGINE':DATABASE_ENGINE, 'PORT':DATABASE_PORT, 'NAME':DATABASE_NAME, 'USER':DATABASE_USER, 'PASSWORD':DATABASE_PASSWORD, 'HOST':DATABASE_HOST}}

