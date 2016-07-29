# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or modify
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


"""DOI Badge Blueprint."""

from __future__ import absolute_import

from flask import Blueprint, abort, redirect, url_for
from sqlalchemy.orm.exc import NoResultFound

from ..api import GitHubRelease
from ..models import Repository

blueprint = Blueprint(
    'invenio_github_badge',
    __name__,
    url_prefix='/badge',
    static_folder='../static',
    template_folder='../templates',
)


def get_badge_image_url(repo, ext='svg'):
    """Return the badge for a DOI."""
    if repo.latest_release:
        release = GitHubRelease(repo.latest_release)
        pid = release.pid
    return url_for('invenio_formatter_badges.badge',
                   title=pid.pid_type,
                   value=pid.pid_value,
                   ext=ext)


#
# Views
#
@blueprint.route('/<int:github_id>.svg')
def index(github_id):
    """Generate a badge for a specific GitHub repository."""
    try:
        repo = Repository.query.filter_by(github_id=github_id).one()
        return redirect(get_badge_image_url(repo))
    except NoResultFound:
        pass
    abort(404)


@blueprint.route('/<int:user_id>/<path:repo_name>.svg')
def index_old(user_id, repo_name):
    """Generate a badge for a specific GitHub repository."""
    try:
        repo = Repository.query.filter_by(name=repo_name).one()
        return redirect(get_badge_image_url(repo))
    except NoResultFound:
        abort(404)


@blueprint.route('/latestdoi/<int:github_id>')
def latest_doi(github_id):
    """Redirect to the newest record version."""
    try:
        repo = Repository.query.filter_by(github_id=github_id).one()
        if repo.latest_release:
            release = GitHubRelease(repo.latest_release)
            return redirect('https://doi.org/{pid}'.format(
                pid=release.pid.pid_value))
    except NoResultFound:
        pass
    abort(404)


@blueprint.route('/latestdoi/<int:user_id>/<path:repo_name>')
def latest_doi_old(user_id, repo_name):
    """Redirect to the newest record version."""
    try:
        repo = Repository.query.filter_by(name=repo_name).one()
        if repo.latest_release:
            release = GitHubRelease(repo.latest_release)
            return redirect('https://doi.org/{pid}'.format(
                pid=release.pid.pid_value))
    except NoResultFound:
        pass
    abort(404)
