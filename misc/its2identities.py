#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors :
#       Daniel Izquierdo-Cortazar <dizquierdo@bitergia.com>

#
# its2identities.py
#
# This script is based on the outcomes of unifypeople.py used in the CVSAnalY
# database. This checks information about name and email from the email accounts
# found in the people table (outcomes of the Bicho tool). If this is found,
# then the table people_upeople is populated with the upeople_id found in identities.
# If not, a new entry in identities table is generated and its correspondant link
# to the people_upeople table.


import MySQLdb
import sys
import re
from optparse import OptionGroup, OptionParser

def getOptions():     
    parser = OptionParser(usage='Usage: %prog [options]', 
                          description='Companies detection using email domains',
                          version='0.1')
    
    parser.add_option('--db-database-its', dest='db_database_its',
                     help='ITS database name', default=None)
    parser.add_option('--db-database-ids', dest='db_database_ids',
                     help='Identities database name', default=None)
    parser.add_option('-u','--db-user', dest='db_user',
                     help='Database user name', default='root')
    parser.add_option('-p', '--db-password', dest='db_password',
                     help='Database user password', default='')
    parser.add_option('--db-hostname', dest='db_hostname',
                     help='Name of the host where database server is running',
                     default='localhost')
    parser.add_option('--db-port', dest='db_port',
                     help='Port of the host where database server is running',
                     default='3306')
    
    (ops, args) = parser.parse_args()
    
    return ops

def connect(db, cfg):
   user = cfg.db_user
   password = cfg.db_password
   host = cfg.db_hostname

   try:
      db = MySQLdb.connect(user = user, passwd = password, db = db)      
      return db, db.cursor()
   except:
      print("Database connection error")
      raise

def execute_query(connector, query):
   results = int (connector.execute(query))
   cont = 0
   if results > 0:
      result1 = connector.fetchall()
      return result1
   else:
      return []

def create_tables(db, connector):
   connector.execute("DROP TABLE IF EXISTS people_upeople")
   connector.execute("""CREATE TABLE people_upeople (
                               people_id int(11) NOT NULL,
                               upeople_id int(11) NOT NULL,
                               PRIMARY KEY (people_id)
                  ) ENGINE=MyISAM DEFAULT CHARSET=utf8""")
   connector.execute("ALTER TABLE people_upeople DISABLE KEYS")
   db.commit()

   return



def main():
   cfg = getOptions()
   
   db_bicho, connector_bts = connect(cfg.db_database_its, cfg)
   db_ids, connector_ids = connect(cfg.db_database_ids, cfg)

   create_tables(db_bicho, connector_bts)

   query = "select id, name, email from people"
   results = execute_query(connector_bts, query)
   for result in results:
      people_id = int(result[0])
      name = result[1]
      name = name.replace("'", "\\'") #avoiding ' errors in MySQL
      email = result[2]
      if email:
          email = email.replace("'", "\\'") #avoiding ' errors in MySQL
      query = "select upeople_id from identities where identity='" + name + "'"
      if email:
        query += " or identity='"+ email +"'"
      query += ";"  
      results_ids = execute_query(connector_ids, query)
      if len(results_ids) > 0:
         # there exist such identity
         upeople_id = int(results_ids[0][0])
         query = "insert into people_upeople(people_id, upeople_id) " +\
                 "values('"+ str(people_id) +"', "+str(upeople_id)+");"
         execute_query(connector_bts, query)
      else:
         #Insert in people_upeople, identities and upeople (new identitiy)
 
         # Max (upeople_)id from upeople table
         query = "select max(id) from upeople;"
         results = execute_query(connector_ids, query)
         upeople_id = int(results[0][0]) + 1
         
         query = "insert into upeople(id) values("+ str(upeople_id) +");"
         execute_query(connector_ids, query)
         
         query = "insert into identities(upeople_id, identity, type)" +\
                 "values(" + str(upeople_id) + ", '"+name+"', 'name');"
         execute_query(connector_ids, query)
 
         if email:
             query = "insert into identities(upeople_id, identity, type)" +\
                     "values(" + str(upeople_id) + ", '"+email+"', 'email');"
             execute_query(connector_ids, query)

         query = "insert into people_upeople(people_id, upeople_id) " +\
                 "values('"+ str(people_id) +"', "+str(upeople_id)+");"
         print query
         execute_query(connector_bts, query)

   db_ids.commit()
   return 



if __name__ == "__main__":main()

