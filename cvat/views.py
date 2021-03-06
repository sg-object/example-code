# Copyright (C) 2021 Intel Corporation
#
# SPDX-License-Identifier: MIT

from django.core.exceptions import BadRequest
from django.utils.functional import SimpleLazyObject
from rest_framework import views, serializers
from rest_framework.exceptions import ValidationError
from django.conf import settings
from rest_framework.response import Response
from rest_auth.registration.views import RegisterView
from allauth.account import app_settings as allauth_settings
from furl import furl

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer, extend_schema_view


from .authentication import Signer
from rest_framework import mixins, serializers, status, viewsets
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from cvat.apps.iam.models import TokenInfo

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now, timedelta

import string
import random

def get_context(request):
    from cvat.apps.organizations.models import Organization, Membership

    IAM_ROLES = {role: priority for priority, role in enumerate(settings.IAM_ROLES)}
    groups = list(request.user.groups.filter(name__in=list(IAM_ROLES.keys())))
    groups.sort(key=lambda group: IAM_ROLES[group.name])

    organization = None
    membership = None
    try:
        org_slug = request.GET.get('org')
        org_id = request.GET.get('org_id')
        org_header = request.headers.get('X-Organization')

        if org_id != None and (org_slug != None or org_header != None):
            raise BadRequest('You cannot specify "org_id" query parameter with ' +
                             '"org" query parameter or "X-Organization" HTTP header at the same time.')
        if org_slug != None and org_header != None and org_slug != org_header:
            raise BadRequest('You cannot specify "org" query parameter and ' +
                             '"X-Organization" HTTP header with different values.')
        org_slug = org_slug if org_slug != None else org_header

        org_filter = None
        if org_slug:
            organization = Organization.objects.get(slug=org_slug)
            membership = Membership.objects.filter(organization=organization,
                                                   user=request.user).first()
            org_filter = {'organization': organization.id}
        elif org_id:
            organization = Organization.objects.get(id=int(org_id))
            membership = Membership.objects.filter(organization=organization,
                                                   user=request.user).first()
            org_filter = {'organization': organization.id}
        elif org_slug is not None:
            org_filter = {'organization': None}
    except Organization.DoesNotExist:
        raise BadRequest(f'{org_slug or org_id} organization does not exist.')

    if membership and not membership.is_active:
        membership = None

    context = {
        "privilege": groups[0] if groups else None,
        "membership": membership,
        "organization": organization,
        "visibility": org_filter,
    }

    return context
class ContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # https://stackoverflow.com/questions/26240832/django-and-middleware-which-uses-request-user-is-always-anonymous
        request.iam_context = SimpleLazyObject(lambda: get_context(request))

        return self.get_response(request)


@extend_schema(tags=['auth'])
@extend_schema_view(post=extend_schema(
    summary='This method signs URL for access to the server',
    description='Signed URL contains a token which authenticates a user on the server.'
                'Signed URL is valid during 30 seconds since signing.',
    request=inline_serializer(
        name='Signing',
        fields={
            'url': serializers.CharField(),
        }
    ),
    responses={'200': OpenApiResponse(response=OpenApiTypes.STR, description='text URL')}))
class SigningView(views.APIView):

    def post(self, request):
        url = request.data.get('url')
        if not url:
            raise ValidationError('Please provide `url` parameter')

        signer = Signer()
        url = self.request.build_absolute_uri(url)
        sign = signer.sign(self.request.user, url)

        url = furl(url).add({Signer.QUERY_PARAM: sign}).url
        return Response(url)


class RegisterViewEx(RegisterView):
    def get_response_data(self, user):
        data = self.get_serializer(user).data
        data['email_verification_required'] = True
        data['key'] = None
        if allauth_settings.EMAIL_VERIFICATION != \
                allauth_settings.EmailVerificationMethod.MANDATORY:
            data['email_verification_required'] = False
            data['key'] = user.auth_token.key
        return data


class PassView(views.APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, user_id):
        GET = request.GET
        META = request.META
        pass_token = META.get('HTTP_PASS_TOKEN')
        token_info = get_object_or_404(TokenInfo, token = pass_token, user_id= user_id)
        token_info.delete()
        print('get pass token info : ' , token_info.created)
        expiry_date = now() - timedelta(seconds=10)
        
        if(token_info.created <= expiry_date):
            print('expiry_date~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        user = get_object_or_404(User, pk = user_id)
        print('get user : ', user.username)

        token = get_object_or_404(Token, user_id = user_id)
        print(token.key)

        data = {
            'token': token.key,
            'user': user.username
        }
        return JsonResponse(data)

class SwaggerPassView(views.APIView):
    permission_classes = []
    def get(self, request):
        user = request.user

        if not user.is_staff and not user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        META = request.META
        authorization = META.get('HTTP_AUTHORIZATION')
        if authorization == None or not authorization.startswith('Token '):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        token_key = authorization[6:]

        get_object_or_404(Token, key = token_key, user_id = user.id)

        token = ''
        string_pool = string.ascii_letters + string.digits
        for i in range(40):
            token += random.choice(string_pool)

        swagger_token = SwaggerToken()
        swagger_token.token = token
        swagger_token.user_id = user.id
        swagger_token.save()

        data = {
            'redirect': '/api/swagger/?token=' + token
        }
        return JsonResponse(data)
