#coding=utf-8
from __future__ import unicode_literals
from django.db import models
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

# Create your models here.
class Department(models.Model):
    d_id = models.AutoField(primary_key=True)
    d_name = models.CharField(max_length=40,unique=True,blank=False)
    d_enname = models.CharField(max_length=30,unique=True,blank=False)
    d_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    d_mtime = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __unicode__(self):
        return str(self.d_id)

class Users(models.Model):
    u_id = models.AutoField(primary_key=True)
    u_name = models.CharField(max_length=30)
    u_enname = models.CharField(max_length=30,unique=True,blank=False)
    u_password = models.CharField(max_length=50)
    u_email = models.EmailField(max_length=50)
    u_role = models.IntegerField(default=1)
    u_purview = models.IntegerField(default=2)
    u_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    u_mtime = models.DateTimeField(auto_now=True, auto_now_add=False)
    u_status = models.BooleanField(default=True)
    department = models.ForeignKey(Department,on_delete=models.SET_NULL,null=True)

    # u_role , 1:other,2:leader
    # u_purview , 1:leader,2:other

    def __unicode__(self):
        return str(self.u_id)

## ticket type
class Ticket_Type(models.Model):
    type_id = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=50,unique=True)
    type_executor = models.ForeignKey(Users)
    type_checkleader = models.CharField(max_length=250)
    type_status = models.BooleanField(default=True)
    type_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    type_mtime = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __unicode__(self):
        return str(self.type_id)

## tickets
class Ticket_Tickets(models.Model):
    ticket_id = models.CharField(max_length=40,primary_key=True)
    ticket_title = models.CharField(max_length=250)
    ticket_type = models.ForeignKey(Ticket_Type,on_delete=models.PROTECT)
    ticket_creator = models.ForeignKey(Users,related_name="ticket_creator")
    ticket_require = models.TextField()
    ticket_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    ticket_result = models.TextField()
    ticket_rtime = models.DateField()
    ticket_executor = models.ForeignKey(Users)
    ticket_checkleader = models.ManyToManyField(Users,related_name="ticket_checkleader",through='Tickets_Users')
    ticket_checksum = models.IntegerField(default=0)
    ticket_status = models.IntegerField()

    def __unicode__(self):
        return str(self.ticket_id)


class Tickets_Users(models.Model):
    tu_id = models.AutoField(primary_key=True)
    ticket_tickets = models.ForeignKey(Ticket_Tickets)  
    users = models.ForeignKey(Users)  
    status = models.IntegerField(default=1)

    def __unicode__(self):
        return str(self.tu_id)

## ticket Operation Record
class Ticket_Operating(models.Model):
    operating_id = models.AutoField(primary_key=True)
    operating_operator = models.ForeignKey(Users)
    operating_type = models.CharField(max_length=50)
    operating_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    operating_content = models.TextField()
    ticket_tickets = models.ForeignKey(Ticket_Tickets) 

    def __unicode__(self):
        return str(self.operating_id)

## ticket Reply to comment
class Ticket_Reply(models.Model):
    reply_id = models.AutoField(primary_key=True)
    reply_author = models.ForeignKey(Users)
    reply_content = models.TextField()
    reply_ctime = models.DateTimeField(auto_now=False, auto_now_add=True)
    reply_mtime = models.DateTimeField(auto_now=True, auto_now_add=False)
    ticket_tickets = models.ForeignKey(Ticket_Tickets) 

    def __unicode__(self):
        return str(self.reply_id)
