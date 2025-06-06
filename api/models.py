from django.db import models


class RRCClient(models.Model):
    """
    Model representing client data.
    This is just a placeholder - you'll use raw SQL for operations.
    """
    code = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    branch = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    software = models.CharField(max_length=100, blank=True, null=True)
    mobile = models.CharField(max_length=50, blank=True, null=True)
    installationdate = models.DateField(blank=True, null=True)
    priorty = models.IntegerField(blank=True, null=True)
    directdealing = models.CharField(max_length=50, blank=True, null=True)
    rout = models.CharField(max_length=100, blank=True, null=True)
    amc = models.CharField(max_length=50, blank=True, null=True)
    amcamt = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    accountcode = models.CharField(max_length=50, blank=True, null=True)
    address3 = models.TextField(blank=True, null=True)
    lictype = models.CharField(max_length=50, blank=True, null=True)
    clients = models.IntegerField(blank=True, null=True)
    sp = models.IntegerField(blank=True, null=True)
    nature = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False  # This model won't be managed by Django migrations
        db_table = 'rrc_clients'
