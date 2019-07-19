#
# SPDX-License-Identifier: Apache-2.0
#
import logging

from django.core.validators import FileExtensionValidator
from rest_framework import serializers
from api.common.enums import (
    Operation,
    NetworkType,
    FabricNodeType,
    FabricVersions,
    HostType,
)
from api.common.serializers import PageQuerySerializer
from api.models import Node, Port, FabricCA, validate_file, NodeUser
from api.utils.common import to_form_paras

LOG = logging.getLogger(__name__)


class NodeQuery(PageQuerySerializer, serializers.ModelSerializer):
    agent_id = serializers.UUIDField(
        help_text="Agent ID, only operator can use this field",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Node
        fields = (
            "page",
            "per_page",
            "type",
            "name",
            "network_type",
            "network_version",
            "agent_id",
        )
        extra_kwargs = {"type": {"required": False}}


class NodeIDSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="ID of node")


class NodeInListSerializer(NodeIDSerializer, serializers.ModelSerializer):
    agent_id = serializers.UUIDField(
        help_text="Agent ID", required=False, allow_null=True
    )
    network_id = serializers.UUIDField(
        help_text="Network ID", required=False, allow_null=True
    )

    class Meta:
        model = Node
        fields = (
            "id",
            "type",
            "name",
            "network_type",
            "network_version",
            "created_at",
            "agent_id",
            "network_id",
            "status",
        )
        extra_kwargs = {
            "id": {"required": True, "read_only": False},
            "created_at": {"required": True, "read_only": False},
        }


class NodeListSerializer(serializers.Serializer):
    data = NodeInListSerializer(many=True, help_text="Nodes list")
    total = serializers.IntegerField(
        help_text="Total number of node", min_value=0
    )


class FabricCASerializer(serializers.ModelSerializer):
    hosts = serializers.ListField(
        help_text="Hosts for ca support",
        child=serializers.CharField(help_text="Host name", max_length=64),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = FabricCA
        fields = ("admin_name", "admin_password", "hosts", "type")


class NodeInfoSerializer(NodeIDSerializer, serializers.ModelSerializer):
    ca = FabricCASerializer(
        help_text="CA configuration for node", required=False, allow_null=True
    )
    file = serializers.URLField(help_text="File url of node", required=False)

    class Meta:
        model = Node
        fields = (
            "id",
            "type",
            "name",
            "network_type",
            "network_version",
            "created_at",
            "agent_id",
            "network_id",
            "status",
            "ca",
            "file",
        )
        extra_kwargs = {
            "id": {"required": True, "read_only": False},
            "created_at": {"required": True, "read_only": False},
        }


class NodeCreateBody(serializers.ModelSerializer):
    agent_type = serializers.ChoiceField(
        help_text="Agent type",
        choices=HostType.to_choices(True),
        required=False,
    )
    ca = FabricCASerializer(
        help_text="CA configuration for node", required=False
    )

    class Meta:
        model = Node
        fields = (
            "network_type",
            "network_version",
            "type",
            "agent_type",
            "agent",
            "ca",
        )
        extra_kwargs = {
            "network_type": {"required": True},
            "network_version": {"required": True},
            "type": {"required": True},
        }

    def validate(self, attrs):
        network_type = attrs.get("network_type")
        node_type = attrs.get("type")
        network_version = attrs.get("network_version")
        agent_type = attrs.get("agent_type")
        agent = attrs.get("agent")
        if network_type == NetworkType.Fabric.name.lower():
            if network_version not in FabricVersions.values():
                raise serializers.ValidationError("Not valid fabric version")
            if node_type not in FabricNodeType.names():
                raise serializers.ValidationError(
                    "Not valid node type for %s" % network_type
                )

        if agent_type is None and agent is None:
            raise serializers.ValidationError("Please set agent_type or agent")

        if agent_type and agent:
            if agent_type != agent.type:
                raise serializers.ValidationError(
                    "agent type not equal to agent"
                )

        return attrs


class PortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Port
        fields = ("external", "internal")
        extra_kwargs = {
            "external": {"required": True},
            "internal": {"required": True},
        }


class NodeUpdateBody(serializers.ModelSerializer):
    ports = PortSerializer(
        help_text="Port mapping for node", many=True, required=False
    )

    class Meta:
        model = Node
        fields = ("status", "ports")


class NodeOperationSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        help_text=Operation.get_info("Operation for node:", list_str=True),
        choices=Operation.to_choices(True),
    )


class NodeFileCreateSerializer(serializers.ModelSerializer):
    def to_form_paras(self):
        custom_paras = to_form_paras(self)

        return custom_paras

    class Meta:
        model = Node
        fields = ("file",)
        extra_kwargs = {
            "file": {
                "required": True,
                "validators": [
                    FileExtensionValidator(
                        allowed_extensions=["tar.gz", "tgz"]
                    ),
                    validate_file,
                ],
            }
        }


class NodeUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeUser
        fields = ("name", "user_type", "secret", "attrs")
        extra_kwargs = {
            "name": {"required": True},
            "user_type": {"required": True},
            "secret": {"required": True},
        }


class NodeUserIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeUser
        fields = ("id",)


class NodeUserPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeUser
        fields = ("status",)
        extra_kwargs = {"status": {"required": True}}