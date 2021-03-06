# Copyright 2013, Google Inc. All rights reserved.
# Use of this source code is governed by a BSD-style license that can
# be found in the LICENSE file.

import struct

from vtdb import dbexceptions
from vtdb import keyrange_constants


pack_keyspace_id = struct.Struct('!Q').pack

# Represent the SrvKeyspace object from the toposerver, and provide functions
# to extract sharding information from the same.
class Keyspace(object):
  name = None
  partitions = None
  sharding_col_name = None
  sharding_col_type = None
  served_from = None

  # load this object from a SrvKeyspace object generated by vt
  def __init__(self, name, data):
    self.name = name
    self.partitions = data.get('Partitions', {})
    self.sharding_col_name = data.get('ShardingColumnName', "")
    self.sharding_col_type = data.get('ShardingColumnType', keyrange_constants.KIT_UNSET)
    self.served_from = data.get('ServedFrom', None)

  def get_shards(self, db_type):
    if not db_type:
      raise ValueError('db_type is not set')
    try:
      return self.partitions[db_type]['ShardReferences']
    except KeyError:
      return []

  def get_shard_count(self, db_type):
    if not db_type:
      raise ValueError('db_type is not set')
    shards = self.get_shards(db_type)
    return len(shards)

  def get_shard_names(self, db_type):
    if not db_type:
      raise ValueError('db_type is not set')
    shards = self.get_shards(db_type)
    return [shard['Name'] for shard in shards]

  def keyspace_id_to_shard_name_for_db_type(self, keyspace_id, db_type):
    if not keyspace_id:
      raise ValueError('keyspace_id is not set')
    if not db_type:
      raise ValueError('db_type is not set')
    # Pack this into big-endian and do a byte-wise comparison.
    pkid = pack_keyspace_id(keyspace_id)
    shards = self.get_shards(db_type)
    for shard in shards:
      if _shard_contain_kid(pkid,
                            shard['KeyRange']['Start'],
                            shard['KeyRange']['End']):
        return shard['Name']
    raise ValueError('cannot find shard for keyspace_id %s in %s' % (keyspace_id, shards))


def _shard_contain_kid(pkid, start, end):
    return start <= pkid and (end == keyrange_constants.MAX_KEY or pkid < end)


def read_keyspace(topo_client, keyspace_name):
  try:
    data = topo_client.get_srv_keyspace('local', keyspace_name)
    if not data:
      raise dbexceptions.OperationalError('invalid empty keyspace',
                                          keyspace_name)
    return Keyspace(keyspace_name, data)
  except dbexceptions.OperationalError as e:
    raise e
  except Exception as e:
    raise dbexceptions.OperationalError('invalid keyspace', keyspace_name, e)
