from django.db import models


class KnownKey(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=12)
    sector = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.key})"
    
    def as_list(self) -> list:
        return [int(self.key[i:i+2], 16) for i in range(0, 12, 2)]
    

class OperationLog(models.Model):
    class Operation(models.TextChoices):
        READ_UID = 'read_uid', 'Read UID'
        READ_BLOCK = 'read_block', 'Read Block'
        WRITE_BLOCK = 'write_block', 'Write Block'
        DUMP = 'dump', 'Dump Card'
        CHANGE_KEY = 'change_key', 'Change Key'
    
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILURE = 'failure', 'Failure'
    
    operation = models.CharField(max_length=20, choices=Operation.choices)
    status = models.CharField(max_length=10, choices=Status.choices)
    uid = models.CharField(max_length=20, blank=True)
    sector = models.IntegerField(null=True, blank=True)
    block = models.IntegerField(null=True, blank=True)
    data = models.TextField(blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.operation} - {self.status} - {self.created_at}"