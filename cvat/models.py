# Copyright (C) 2021 Intel Corporation
#
# SPDX-License-Identifier: MIT
from django.db import models

class TokenInfo(models.Model):
    token = models.CharField(primary_key=True, max_length=50)
    user_id = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'token_info'