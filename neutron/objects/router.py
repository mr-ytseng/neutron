#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import netaddr

from oslo_versionedobjects import base as obj_base
from oslo_versionedobjects import fields as obj_fields
from sqlalchemy import func

from neutron.common import utils
from neutron.db.models import l3
from neutron.db.models import l3_attrs
from neutron.db.models import l3agent as rb_model
from neutron.extensions import availability_zone as az_ext
from neutron.objects import base
from neutron.objects import common_types


@obj_base.VersionedObjectRegistry.register
class RouterRoute(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = l3.RouterRoute

    fields = {
        'router_id': common_types.UUIDField(),
        'destination': common_types.IPNetworkField(),
        'nexthop': obj_fields.IPAddressField()
    }

    primary_keys = ['router_id', 'destination', 'nexthop']
    foreign_keys = {'Router': {'router_id': 'id'}}

    @classmethod
    def modify_fields_from_db(cls, db_obj):
        result = super(RouterRoute, cls).modify_fields_from_db(db_obj)
        if 'destination' in result:
            result['destination'] = utils.AuthenticIPNetwork(
                result['destination'])
        if 'nexthop' in result:
            result['nexthop'] = netaddr.IPAddress(result['nexthop'])
        return result

    @classmethod
    def modify_fields_to_db(cls, fields):
        result = super(RouterRoute, cls).modify_fields_to_db(fields)
        if 'destination' in result:
            result['destination'] = cls.filter_to_str(result['destination'])
        if 'nexthop' in result:
            result['nexthop'] = cls.filter_to_str(result['nexthop'])
        return result


@obj_base.VersionedObjectRegistry.register
class RouterExtraAttributes(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = l3_attrs.RouterExtraAttributes

    fields = {
        'router_id': common_types.UUIDField(),
        'distributed': obj_fields.BooleanField(default=False),
        'service_router': obj_fields.BooleanField(default=False),
        'ha': obj_fields.BooleanField(default=False),
        'ha_vr_id': obj_fields.IntegerField(nullable=True),
        'availability_zone_hints': obj_fields.ListOfStringsField(nullable=True)
    }

    primary_keys = ['router_id']

    foreign_keys = {'Router': {'router_id': 'id'}}

    @classmethod
    def modify_fields_from_db(cls, db_obj):
        result = super(RouterExtraAttributes, cls).modify_fields_from_db(
            db_obj)
        if az_ext.AZ_HINTS in result:
            result[az_ext.AZ_HINTS] = (
                az_ext.convert_az_string_to_list(result[az_ext.AZ_HINTS]))
        return result

    @classmethod
    def modify_fields_to_db(cls, fields):
        result = super(RouterExtraAttributes, cls).modify_fields_to_db(fields)
        if az_ext.AZ_HINTS in result:
            result[az_ext.AZ_HINTS] = (
                az_ext.convert_az_list_to_string(result[az_ext.AZ_HINTS]))
        return result

    @classmethod
    def get_router_agents_count(cls, context):
        # TODO(sshank): This is pulled out from l3_agentschedulers_db.py
        # until a way to handle joins is figured out.
        binding_model = rb_model.RouterL3AgentBinding
        sub_query = (context.session.query(
            binding_model.router_id,
            func.count(binding_model.router_id).label('count')).
                     join(l3_attrs.RouterExtraAttributes,
                          binding_model.router_id ==
                          l3_attrs.RouterExtraAttributes.router_id).
                     join(l3.Router).
                     group_by(binding_model.router_id).subquery())

        query = (context.session.query(l3.Router, sub_query.c.count).
                 outerjoin(sub_query))

        return [(router, agent_count) for router, agent_count in query]


@obj_base.VersionedObjectRegistry.register
class RouterPort(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = l3.RouterPort

    primary_keys = ['router_id', 'port_id']

    foreign_keys = {'Router': {'router_id': 'id'}}

    fields = {
        'router_id': common_types.UUIDField(),
        'port_id': common_types.UUIDField(),
        'port_type': obj_fields.StringField(nullable=True),
    }
