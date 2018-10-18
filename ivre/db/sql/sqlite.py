#! /usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of IVRE.
# Copyright 2011 - 2018 Pierre LALET <pierre.lalet@cea.fr>
#
# IVRE is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IVRE is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IVRE. If not, see <http://www.gnu.org/licenses/>.

"""This sub-module contains functions to interact with SQLite
databases.

"""


from sqlalchemy import func, insert, update, and_
from sqlalchemy.exc import IntegrityError

from ivre import utils
from ivre.db.sql import SQLDB, SQLDBPassive


class SqliteDB(SQLDB):

    def __init__(self, url):
        SQLDB.__init__(self, url)


class SqliteDBPassive(SqliteDB, SQLDBPassive):

    def __init__(self, url):
        SqliteDB.__init__(self, url)
        SQLDBPassive.__init__(self, url)

    def _insert_or_update(self, timestamp, values, lastseen=None):
        stmt = insert(self.tables.passive)\
            .values(dict(values, addr=utils.force_int2ip(values['addr'])))
        try:
            self.db.execute(stmt)
        except IntegrityError:
            whereclause = and_(
                self.tables.passive.addr == values['addr'],
                self.tables.passive.sensor == values['sensor'],
                self.tables.passive.recontype == values['recontype'],
                self.tables.passive.source == values['source'],
                self.tables.passive.value == values['value'],
                self.tables.passive.targetval == values['targetval'],
                self.tables.passive.info == values['info'],
                self.tables.passive.port == values['port']
            )
            upsert = {
                'firstseen': func.least(
                    self.tables.passive.firstseen,
                    timestamp,
                ),
                'lastseen': func.greatest(
                    self.tables.passive.lastseen,
                    lastseen or timestamp,
                ),
                'count': self.tables.passive.count + values['count'],
            }
            updt = update(
                self.tables.passive
            ).where(whereclause).values(upsert)
            self.db.execute(updt)