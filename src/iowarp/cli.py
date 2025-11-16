"""
Unified CLI for IOWarp ecosystem.

This module provides a unified command-line interface that integrates
iowarp-core and iowarp-agent-toolkit functionality.
"""

import sys
import click
from importlib.metadata import version, PackageNotFoundError


def get_version():
    """Get the iowarp package version."""
    try:
        return version("iowarp")
    except PackageNotFoundError:
        return "0.0.0.dev0"


@click.group(invoke_without_command=True)
@click.option('--version', 'show_version', is_flag=True, help='Show version and exit')
@click.pass_context
def main(ctx, show_version):
    """
    IOWarp - Unified interface for high-performance I/O and AI agent tools.

    When run without subcommands, starts the IOWarp runtime (iowarp-core).

    Use 'iowarp core' for core runtime commands.
    Use 'iowarp agent' for AI agent toolkit commands.
    """
    if show_version:
        click.echo(f"iowarp {get_version()}")
        ctx.exit()

    # If no subcommand is provided, run the default action (start runtime)
    if ctx.invoked_subcommand is None:
        try:
            from iowarp_core._cli import chimaera_start_runtime
            click.echo("Starting IOWarp runtime (iowarp-core)...")
            chimaera_start_runtime()
        except ImportError:
            click.echo("Error: iowarp-core is not installed or not functional yet.", err=True)
            click.echo("Install it with: pip install iowarp-core", err=True)
            ctx.exit(1)
        except Exception as e:
            click.echo(f"Error starting runtime: {e}", err=True)
            ctx.exit(1)


@main.group(name='core')
def core_group():
    """IOWarp Core runtime commands."""
    pass


@core_group.command(name='start')
@click.pass_context
def core_start(ctx):
    """Start the IOWarp runtime."""
    try:
        from iowarp_core._cli import chimaera_start_runtime
        chimaera_start_runtime()
    except ImportError:
        click.echo("Error: iowarp-core is not installed.", err=True)
        ctx.exit(1)


@core_group.command(name='stop')
@click.pass_context
def core_stop(ctx):
    """Stop the IOWarp runtime."""
    try:
        from iowarp_core._cli import chimaera_stop_runtime
        chimaera_stop_runtime()
    except ImportError:
        click.echo("Error: iowarp-core is not installed.", err=True)
        ctx.exit(1)


@core_group.command(name='compose')
@click.pass_context
def core_compose(ctx):
    """Compose IOWarp runtime configuration."""
    try:
        from iowarp_core._cli import chimaera_compose
        chimaera_compose()
    except ImportError:
        click.echo("Error: iowarp-core is not installed.", err=True)
        ctx.exit(1)


@core_group.command(name='refresh')
@click.pass_context
def core_refresh(ctx):
    """Refresh IOWarp repository."""
    try:
        from iowarp_core._cli import chi_refresh_repo
        chi_refresh_repo()
    except ImportError:
        click.echo("Error: iowarp-core is not installed.", err=True)
        ctx.exit(1)


@main.group(name='agent')
def agent_group():
    """IOWarp Agent Toolkit commands."""
    pass


@agent_group.command(name='mcp-server')
@click.argument('server_name')
@click.argument('args', nargs=-1)
@click.pass_context
def agent_mcp_server(ctx, server_name, args):
    """Run an MCP server by name."""
    try:
        from agent_toolkit import run_mcp_server
        run_mcp_server(server_name, list(args))
    except ImportError:
        click.echo("Error: iowarp-agent-toolkit is not installed.", err=True)
        ctx.exit(1)


@agent_group.command(name='mcp-servers')
@click.pass_context
def agent_mcp_servers(ctx):
    """List all available MCP servers."""
    try:
        from agent_toolkit import list_mcp_servers
        list_mcp_servers()
    except ImportError:
        click.echo("Error: iowarp-agent-toolkit is not installed.", err=True)
        ctx.exit(1)


@agent_group.command(name='prompt')
@click.argument('prompt_name')
@click.pass_context
def agent_prompt(ctx, prompt_name):
    """Print a prompt template to stdout."""
    try:
        from agent_toolkit import print_prompt
        print_prompt(prompt_name)
    except ImportError:
        click.echo("Error: iowarp-agent-toolkit is not installed.", err=True)
        ctx.exit(1)


@agent_group.command(name='prompts')
@click.pass_context
def agent_prompts(ctx):
    """List all available prompt templates."""
    try:
        from agent_toolkit import list_prompts
        list_prompts()
    except ImportError:
        click.echo("Error: iowarp-agent-toolkit is not installed.", err=True)
        ctx.exit(1)


if __name__ == '__main__':
    main()
