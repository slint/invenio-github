# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Configuration for GitHub module."""

GITHUB_WEBHOOK_RECEIVER_ID = 'github'
"""Local name of webhook receiver."""

GITHUB_WEBHOOK_RECEIVER_URL = None
"""URL format to be used when creating a webhook on GitHub.

This configuration variable must be set explicitly. Example::

  http://localhost:5000/api/receivers/github/events/?access_token={token}

.. note::

  This config variable is used because using `url_for` to get and external
  url of an `invenio_base.api_bluebrint`, while inside the regular app
  context, doesn't work.
"""

GITHUB_SHARED_SECRET = 'CHANGEME'
"""Shared secret between you and GitHub.

Used to make GitHub sign webhook requests with HMAC.

See http://developer.github.com/v3/repos/hooks/#example
"""

GITHUB_INSECURE_SSL = False
"""Determine if the GitHub webhook request will check the SSL certificate.

Never set to True in a production environment, but can be useful for
development and integration servers.
"""

GITHUB_RELEASE_CLASS = 'invenio_github.api:GitHubRelease'
"""GitHubRelease class to be used for release handling."""

GITHUB_METADATA_FILE = '.zenodo.json'
"""File with extra metadata stored in GitHub repository."""

GITHUB_DEPOSIT_CLASS = 'invenio_deposit.api:Deposit'
"""Deposit class that implements a `publish` method."""

GITHUB_PID_FETCHER = 'recid'
"""PID Fetcher for Release records."""

GITHUB_REMOTE_APP = dict(
    title='GitHub',
    description='Software collaboration platform.',
    icon='fa fa-github',
    authorized_handler='invenio_oauthclient.handlers'
                       ':authorized_signup_handler',
    disconnect_handler='invenio_github.handlers:disconnect',
    signup_handler=dict(
        info='invenio_oauthclient.contrib.github:account_info',
        setup='invenio_github.handlers:account_setup',
        view='invenio_oauthclient.handlers:signup_handler',
    ),
    params=dict(
        request_token_params={'scope': 'user,admin:repo_hook,read:org'},
        base_url='https://api.github.com/',
        request_token_url=None,
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_method='POST',
        authorize_url='https://github.com/login/oauth/authorize',
        app_key='GITHUB_APP_CREDENTIALS',
    )
)
"""OAuth Client configuration."""
