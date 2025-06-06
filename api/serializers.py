from rest_framework import serializers


class RRCClientSerializer(serializers.Serializer):
    """
    Serializer for handling client data validation and transformation.
    """
    code = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    name = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    address = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    branch = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    district = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    state = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    software = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    mobile = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    installationdate = serializers.DateField(required=False, allow_null=True)
    priorty = serializers.IntegerField(required=False, allow_null=True)
    directdealing = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    rout = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    amc = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    amcamt = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True)
    accountcode = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    address3 = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    lictype = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
    clients = serializers.IntegerField(required=False, allow_null=True)
    sp = serializers.IntegerField(required=False, allow_null=True)
    nature = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)
