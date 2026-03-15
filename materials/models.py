from django.db import models

# Create your models here.

class Kategorija(models.Model):
    idkat = models.AutoField(db_column='IdKat', primary_key=True)  # Field name made lowercase.
    naziv = models.CharField(db_column='Naziv', max_length=20, blank=True, null=True)  # Field name made lowercase.
    tip = models.CharField(db_column='Tip', max_length=20, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'kategorija'


class KategorijaNad(models.Model):
    idkatnad = models.ForeignKey(Kategorija, models.DO_NOTHING, db_column='IdKatNad', primary_key=True)  # Field name made lowercase. The composite primary key (IdKatNad, IdKatPod) found, that is not supported. The first column is selected.
    idkatpod = models.ForeignKey(Kategorija, models.DO_NOTHING, db_column='IdKatPod', related_name='kategorijanad_idkatpod_set')  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'kategorija_nad'
        unique_together = (('idkatnad', 'idkatpod'),)

class Skripta(models.Model):
    idskr = models.AutoField(db_column='IdSkr', primary_key=True)  # Field name made lowercase.
    idkor = models.ForeignKey('accounts.Korisnik', models.DO_NOTHING, db_column='IdKor', blank=True, null=True)  # Field name made lowercase.
    idkat = models.ForeignKey(Kategorija, models.DO_NOTHING, db_column='IdKat')  # Field name made lowercase.
    naziv = models.CharField(db_column='Naziv', max_length=50)  # Field name made lowercase.
    opis = models.CharField(db_column='Opis', max_length=255, blank=True, null=True)  # Field name made lowercase.
    fajl = models.FileField(db_column='Fajl', upload_to='skripte/')  # Field name made lowercase.
    odobrena = models.IntegerField(db_column='Odobrena', default=0)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'skripta'


class Komentar(models.Model):
    idkor = models.ForeignKey('accounts.Korisnik', models.DO_NOTHING, db_column='IdKor', primary_key=True)  # Field name made lowercase. The composite primary key (IdKor, IdSkr) found, that is not supported. The first column is selected.
    idskr = models.ForeignKey(Skripta, models.DO_NOTHING, db_column='IdSkr')  # Field name made lowercase.
    tekst = models.CharField(db_column='Tekst', max_length=512, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'komentar'
        unique_together = (('idkor', 'idskr'),)

class Ocena(models.Model):
    idkor = models.ForeignKey('accounts.Korisnik', models.DO_NOTHING, db_column='IdKor', primary_key=True)  # Field name made lowercase. The composite primary key (IdKor, IdSkr) found, that is not supported. The first column is selected.
    idskr = models.ForeignKey(Skripta, models.DO_NOTHING, db_column='IdSkr')  # Field name made lowercase.
    ocena = models.IntegerField(db_column='Ocena', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'ocena'
        unique_together = (('idkor', 'idskr'),)

class Sacuvano(models.Model):
    idkor = models.ForeignKey('accounts.Korisnik'    , models.DO_NOTHING, db_column='IdKor', primary_key=True)  # Field name made lowercase. The composite primary key (IdKor, IdSkr) found, that is not supported. The first column is selected.
    idskr = models.ForeignKey(Skripta, models.DO_NOTHING, db_column='IdSkr')  # Field name made lowercase.
    kolekcija = models.CharField(db_column='Kolekcija', max_length=18, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'sacuvano'
        unique_together = (('idkor', 'idskr'),)
