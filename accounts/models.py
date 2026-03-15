from django.db import models

# Create your models here.

class Role(models.Model):
    idrol = models.AutoField(db_column='IdRol', primary_key=True)  # Field name made lowercase.
    opis = models.CharField(db_column='Opis', max_length=20)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'role'

class Korisnik(models.Model):
    idkor = models.AutoField(db_column='IdKor', primary_key=True)  # Field name made lowercase.
    idrol = models.ForeignKey(Role, models.DO_NOTHING, db_column='IdRol', default=3)  # Field name made lowercase.
    kor_ime = models.CharField(db_column='Kor_Ime', max_length=20)  # Field name made lowercase.
    lozinka = models.CharField(db_column='Lozinka', max_length=500)  # Field name made lowercase.
    email = models.CharField(db_column='Email', max_length=100)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'korisnik'

class Prijateljstvo(models.Model):
    idkor1 = models.ForeignKey(Korisnik, models.DO_NOTHING, db_column='IdKor1', primary_key=True)  # Field name made lowercase. The composite primary key (IdKor1, IdKor2) found, that is not supported. The first column is selected.
    idkor2 = models.ForeignKey(Korisnik, models.DO_NOTHING, db_column='IdKor2', related_name='prijateljstvo_idkor2_set')  # Field name made lowercase.
    status = models.CharField(db_column='Status', max_length=20)  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'prijateljstvo'
        unique_together = (('idkor1', 'idkor2'),)
