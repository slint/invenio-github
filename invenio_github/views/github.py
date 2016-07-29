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

"""GitHub blueprint for Invenio platform."""

from __future__ import absolute_import

import json
from datetime import datetime

import humanize
import pytz
from dateutil.parser import parse
from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_babelex import gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from invenio_db import db

from ..api import GitHubAPI
from ..models import Repository
from ..utils import parse_timestamp, utcnow

blueprint = Blueprint(
    'invenio_github',
    __name__,
    static_folder='../static',
    template_folder='../templates',
    url_prefix='/account/settings/github',
)


#
# Template filters
#
@blueprint.app_template_filter('naturaltime')
def naturaltime(val):
    """Get humanized version of time."""
    val = val.replace(tzinfo=pytz.utc) \
        if isinstance(val, datetime) else parse(val)
    now = datetime.utcnow().replace(tzinfo=pytz.utc)

    return humanize.naturaltime(now - val)


@blueprint.app_template_filter('prettyjson')
def prettyjson(val):
    """Get pretty-printed json."""
    return json.dumps(json.loads(val), indent=4)


#
# Views
#
@blueprint.route('/', methods=['GET', 'POST'])
@login_required
@register_menu(
    blueprint, 'settings.github',
    _('<i class="fa fa-github fa-fw"></i> GitHub'),
    order=10,
    active_when=lambda: request.endpoint.startswith('invenio_github.')
)
@register_breadcrumb(blueprint, 'breadcrumbs.settings.github', _('GitHub'))
def index():
    """Display list of the user's repositories."""
    github = GitHubAPI(user_id=current_user.get_id())
    token = github.session_token
    ctx = dict(connected=False)

    if token and github.check_token(token.access_token):
        # The user is authenticated and the token we have is still valid.
        if github.account.extra_data.get('login') is None:
            github.init_account()
            db.session.commit()

        # Sync if needed
        if github.check_sync(force=request.method == 'POST'):
            # When we're in an XHR request, we want to synchronously sync hooks
            github.sync(async_hooks=(not request.is_xhr))
            db.session.commit()

        # Generate the repositories view object
        extra_data = github.account.extra_data
        repos = extra_data['repos']
        if repos:
            # 'Enhance' our repos dict, from our database model
            db_repos = Repository.query.filter(
                Repository.github_id.in_([int(k) for k in repos.keys()]),
            ).all()
            for repo in db_repos:
                repos[str(repo.github_id)]['instance'] = repo
                repos[str(repo.github_id)]['latest'] = repo.latest_release

        last_sync = humanize.naturaltime(
            (utcnow() - parse_timestamp(extra_data['last_sync'])))

        ctx.update({
            'connected': True,
            'repos': sorted(repos.items(), key=lambda x: x[1]['full_name']),
            'last_sync': last_sync,
        })

    return render_template('invenio_github/settings/index.html', **ctx)


@blueprint.route('/repository/<path:name>')
@login_required
@register_breadcrumb(blueprint, 'breadcrumbs.settings.github.repo',
                     _('Repository'))
def repository(name):
    """Display selected repository."""
    user_id = current_user.get_id()
    github = GitHubAPI(user_id=user_id)
    token = github.session_token

    if token and github.check_token(token.access_token):
        repos = github.account.extra_data.get('repos', [])
        repo = next((repo for repo_id, repo in repos.items()
                     if repo.get('full_name') == name), {})
        if not repo:
            abort(403)

        # FIXME: Use just filter and check GitHub API for permissions instead
        repo_instance = Repository.get(user_id=user_id, github_id=repo['id'])
        return render_template(
            'invenio_github/settings/view.html',
            repo=repo_instance or Repository(name=repo['full_name'],
                                             github_id=repo['id']),
            releases=(repo_instance.releases.order_by('created desc').all()
                      if repo_instance else []),
        )

    abort(403)


@blueprint.route('/faq')
@login_required
def faq():
    """Display FAQ."""
    return render_template('invenio_github/settings/faq.html')


@blueprint.route('/rejected')
@login_required
def rejected():
    """View for when user rejects request to connect to github."""
    return render_template('invenio_github/settings/rejected.html')


@blueprint.route('/hook', methods=['POST', 'DELETE'])
@login_required
def hook():
    """Install or remove GitHub webhook."""
    repo_id = request.json['id']

    github = GitHubAPI(user_id=current_user.get_id())
    repos = github.account.extra_data['repos']

    if repo_id not in repos:
        abort(404)

    if request.method == 'DELETE':
        try:
            if github.remove_hook(repo_id, repos[repo_id]['full_name']):
                db.session.commit()
                return '', 204
            else:
                abort(400)
        except Exception:
            abort(403)
    elif request.method == 'POST':
        try:
            if github.create_hook(repo_id, repos[repo_id]['full_name']):
                db.session.commit()
                return '', 201
            else:
                abort(400)
        except Exception:
            abort(403)
    else:
        abort(400)


@blueprint.route('/hook/<action>/<repo_id>')
@login_required
def hook_action(action, repo_id):
    """Display selected repository."""
    github = GitHubAPI(user_id=current_user.get_id())
    repos = github.account.extra_data['repos']

    if repo_id not in repos:
        abort(404)

    if action == 'disable':
        if github.remove_hook(repo_id, repos[repo_id]['full_name']):
            db.session.commit()
            return redirect(url_for('.index'))
        else:
            abort(400)
    elif action == 'enable':
        if github.create_hook(repo_id, repos[repo_id]['full_name']):
            db.session.commit()
            return redirect(url_for('.index'))
        else:
            abort(400)
    else:
        abort(400)
