from django.db import models

class Events(models.Model):
    tripdate = models.ForeignKey('Trips', models.DO_NOTHING, db_column='tripdate', blank=False, null=False, primary_key=True, unique=False)
    lat = models.CharField(max_length=255, blank=False, null=False)
    lon = models.CharField(max_length=255, blank=False, null=False)
    speed = models.CharField(max_length=255, blank=False, null=False)
    xacc = models.CharField(max_length=255, blank=False, null=False)
    yacc = models.CharField(max_length=255, blank=False, null=False)
    sec = models.CharField(max_length=255, blank=False, null=False)
    flags = models.CharField(max_length=255, blank=False, null=False)

    def __str__(self):
        return f'{self.tripdate}, {self.lat}, {self.lon}, {self.flags}'

    class Meta:
        managed = False
        db_table = 'events'


class Trips(models.Model):
    tripdate = models.CharField(primary_key=True, max_length=255)

    def __str__(self):
        return self.tripdate

    class Meta:
        managed = False
        db_table = 'trips'
