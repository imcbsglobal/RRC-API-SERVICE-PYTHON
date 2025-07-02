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


class AccProduct(models.Model):
    code = models.CharField(max_length=30, blank=False, null=False)
    name = models.CharField(max_length=200, blank=True, null=True)
    catagory = models.CharField(max_length=20, blank=True, null=True)
    unit = models.CharField(max_length=10, blank=True, null=True)
    taxcode = models.CharField(max_length=5, blank=True, null=True)
    company = models.CharField(max_length=30, blank=True, null=True)
    product = models.CharField(max_length=30, blank=True, null=True)
    brand = models.CharField(max_length=30, blank=True, null=True)
    text6 = models.CharField(max_length=40, blank=True, null=True)

    class Meta:
        managed = False  # No migrations; Django doesn't manage the table
        db_table = 'acc_product'


class AccMaster(models.Model):
    code = models.CharField(max_length=30, blank=False, null=False)
    name = models.CharField(max_length=250, blank=False, null=False)
    super_code = models.CharField(max_length=5, blank=True, null=True)
    opening_balance = models.DecimalField(
        max_digits=12, decimal_places=3, blank=True, null=True)
    debit = models.DecimalField(
        max_digits=16, decimal_places=3, blank=True, null=True)
    credit = models.DecimalField(
        max_digits=16, decimal_places=3, blank=True, null=True)
    place = models.CharField(max_length=60, blank=True, null=True)
    phone2 = models.CharField(max_length=60, blank=True, null=True)
    openingdepartment = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False  # No migrations; Django doesn't manage the table
        db_table = 'acc_master'
