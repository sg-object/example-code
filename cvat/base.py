
SPECTACULAR_SETTINGS = {
    'TITLE': 'CVAT REST API',
    'DESCRIPTION': 'REST API for Computer Vision Annotation Tool (CVAT)',
    # Statically set schema version. May also be an empty string. When used together with
    # view versioning, will become '0.0.0 (v2)' for 'v2' versioned requests.
    # Set VERSION to None if only the request version should be rendered.
    'VERSION': 'alpha',
    'CONTACT': {
        'name': 'Nikita Manovich',
        'url': 'https://github.com/nmanovic',
        'email': 'nikita.manovich@intel.com',
    },
    'LICENSE': {
        'name': 'MIT License',
        'url': 'https://en.wikipedia.org/wiki/MIT_License',
    },
    'SERVE_PUBLIC': True,
    'SCHEMA_COERCE_PATH_PK_SUFFIX': True,
    'SCHEMA_PATH_PREFIX': '/api',
    'SCHEMA_PATH_PREFIX_TRIM': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated', 'cvat.apps.iam.permissions.IsStaffMember'],
    # https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'displayOperationId': True,
        'displayRequestDuration': True,
        'filter': True,
        'showExtensions': True,
    },
    'TOS': 'https://www.google.com/policies/terms/',
    'EXTERNAL_DOCS': {
        'description': 'CVAT documentation',
        'url': 'https://openvinotoolkit.github.io/cvat/docs/',
    },
    # OTHER SETTINGS
    # https://drf-spectacular.readthedocs.io/en/latest/settings.html
}
