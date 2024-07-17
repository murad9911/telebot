# ad_utils.py

from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, Tls
from config import AD_SERVER, AD_USERNAME, AD_PASSWORD, BASE_DN
import logging
import ssl
logger = logging.getLogger(__name__)
def get_user_by_phone(phone_number):
    server = Server(AD_SERVER, get_info=ALL)
    conn = Connection(server, user=AD_USERNAME, password=AD_PASSWORD, auto_bind=True)
    conn.search(BASE_DN, '(mobile={})'.format(phone_number), attributes=['sAMAccountName', 'lockoutTime'])
    user = conn.entries[0] if conn.entries else None
    conn.unbind()
    return user

def unlock_user(username_dn):
    server = Server(AD_SERVER, get_info=ALL)
    conn = Connection(server, user=AD_USERNAME, password=AD_PASSWORD, auto_bind=True)
    conn.modify(username_dn, {'lockoutTime': [(MODIFY_REPLACE, [0])]})
    conn.unbind()

def reset_user_password(username_dn, new_password):
    try:
        server = Server(AD_SERVER, port=636, use_ssl=True, get_info=ALL) 
        conn = Connection(server, user=AD_USERNAME, password=AD_PASSWORD, auto_bind=True, authentication='SIMPLE', client_strategy='SYNC', read_only=False, raise_exceptions=True)
        
        changes = {'unicodePwd': [(MODIFY_REPLACE, [f'"{new_password}"'.encode('utf-16-le')])]}
        conn.modify(username_dn, changes)

        if conn.result['result'] == 0:
            logger.info(f"Password successfully reset for {username_dn}")
        else:
            logger.error(f"Failed to reset password for {username_dn}: {conn.result}")
        
        conn.unbind()
    except Exception as e:
        logger.error(f"Error resetting password for {username_dn}: {str(e)}")
