# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
#
"""User management commands"""

import base64
import json
import datetime
import time

import click

from . import Args, catch_error, echo_json, get_api, kci


@kci.group(name='user')
def kci_user():
    """Interact with user accounts"""


@kci_user.command(secrets=True)
@Args.config
@Args.api
@Args.indent
@catch_error
def whoami(config, api, indent, secrets):
    """Show the current user"""
    api = get_api(config, api, secrets)
    user = api.user.whoami()
    echo_json(user, indent)


def _b64url_decode(data: str) -> bytes:
    """Decode base64url data with padding."""
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _decode_jwt(token: str) -> dict:
    """Decode a JWT without verifying signature."""
    parts = token.split('.')
    if len(parts) != 3:
        raise click.ClickException("Invalid JWT format; expected 3 parts")
    try:
        header = json.loads(_b64url_decode(parts[0]).decode('utf-8'))
        payload = json.loads(_b64url_decode(parts[1]).decode('utf-8'))
    except (ValueError, json.JSONDecodeError) as exc:
        raise click.ClickException("Invalid JWT encoding") from exc
    return {"header": header, "payload": payload}


@kci_user.command(secrets=True, name='token-info')
@click.option('--token', help="JWT token to decode (defaults to API token)")
@click.option('--raw', is_flag=True, help="Print raw JSON data")
@Args.api
@Args.indent
@catch_error
def token_info(token, raw, api, indent, secrets):
    """Decode a JWT and report expiration status"""
    token = token or (secrets.api.token if secrets else None)
    if not token:
        raise click.ClickException(
            "No token provided and no API token found; use --token or set "
            f"kci.secrets.api.<name>.token and pass --api (current: {api})"
        )

    data = _decode_jwt(token)
    if api:
        data["api"] = api
    payload = data.get("payload", {})
    exp = payload.get("exp")
    now = int(time.time())
    exp_info = None
    if isinstance(exp, (int, float)):
        exp_int = int(exp)
        exp_info = {
            "exp": exp_int,
            "now": now,
            "expired": exp_int <= now,
            "expires_in_seconds": max(0, exp_int - now),
        }
    data["expiration"] = exp_info

    if raw:
        echo_json(data, indent)
        return

    header = data.get("header") or {}
    click.echo("Token information:")
    if api:
        click.echo(f"  API config: {api}")
    click.echo(f"  Algorithm: {header.get('alg', 'unknown')}")
    click.echo(f"  Type: {header.get('typ', 'unknown')}")

    if exp_info is None:
        click.echo("  Expiration: not present")
        return

    exp_dt = datetime.datetime.utcfromtimestamp(exp_info["exp"])
    now_dt = datetime.datetime.utcfromtimestamp(exp_info["now"])
    click.echo(f"  Expires (UTC): {exp_dt.isoformat()}Z")
    click.echo(f"  Now (UTC): {now_dt.isoformat()}Z")
    click.echo(f"  Expired: {str(exp_info['expired']).lower()}")
    click.echo(f"  Expires in (seconds): {exp_info['expires_in_seconds']}")
