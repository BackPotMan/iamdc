from __future__ import unicode_literals
from django.db import models

# Create your models here.

class department(models.Model):
    d_id = models.AutoField(primary_key=True)
    d_name = models.CharField(max_length=40,unique=True,blank=False)
    d_enname = models.CharField(max_length=30,unique=True,blank=False)
    d_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    d_mtime = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __unicode__(self):
        return str(self.d_id)

class users(models.Model):
    u_id = models.AutoField(primary_key=True)
    u_name = models.CharField(max_length=30)
    u_enname = models.CharField(max_length=30,unique=True,blank=False)
    u_password = models.CharField(max_length=50)
    u_email = models.EmailField(max_length=50)
    u_role = models.IntegerField(default=1)
    u_purview = models.IntegerField(default=1)
    u_department = models.ForeignKey(department,on_delete=models.SET_NULL,null=True)
    u_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    u_mtime = models.DateTimeField(auto_now=True, auto_now_add=False)


    # u_role , 1:普通用户,2:部门负责人
    # u_purview , 1:后台管理员,2:普通用户

    def __unicode__(self):
        return str(self.u_id)

## ticket type
class ticket_type(models.Model):
    type_id = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=50,unique=True)
    type_principal = models.CharField(max_length=30)
    type_flow = models.CharField(max_length=250)
    type_status = models.BooleanField(default=True)
    type_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    type_mtime = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __unicode__(self):
        return str(self.type_id)


## tickets
class tickets(models.Model):
    ticket_id = models.CharField(max_length=40,primary_key=True)
    ticket_title = models.CharField(max_length=150)
    ticket_type = models.ForeignKey(ticket_type,on_delete=models.PROTECT)
    ticket_principal = models.CharField(max_length=30,null=False)
    ticket_checkper = models.CharField(max_length=30,null=False)
    ticket_checksum = models.IntegerField(default=0)
    ticket_require = models.TextField()
    ticket_creator = models.CharField(max_length=30,null=False)
    ticket_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    ticket_result = models.TextField()
    ticket_rtime = models.DateField()
    ticket_status = models.IntegerField()

    def __unicode__(self):
        return str(self.ticket_id)

## ticket Operation Record
class ticket_operating(models.Model):
    ticket = models.ForeignKey(tickets)
    operating_id = models.AutoField(primary_key=True)
    operating_per = models.CharField(max_length=30)
    operating_type = models.IntegerField()
    operating_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    operating_content = models.TextField()

    def __unicode__(self):
        return str(self.operating_id)

## ticket Reply to comment
class ticket_reply(models.Model):
    ticket = models.ForeignKey(tickets)
    reply_id = models.AutoField(primary_key=True)
    reply_author = models.CharField(max_length=30)
    reply_content = models.TextField()
    reply_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    reply_mtime = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __unicode__(self):
        return str(self.reply_id)




