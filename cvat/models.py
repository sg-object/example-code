from django.db import models

class TokenInfo(models.Model):
    token = models.CharField(primary_key=True, max_length=50)
    user_id = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'token_info'

class SwaggerToken(models.Model):
    token = models.CharField(primary_key=True, max_length=40)
    user_id = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'swagger_token'

class Label(models.Model):
    task = models.ForeignKey(Task, null=True, blank=True, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE)
    name = SafeCharField(max_length=64)
    color = models.CharField(default='', max_length=8)

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = ()
        unique_together = ('task', 'name')
        ordering = ['id']
