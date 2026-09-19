"""Workflow JSON v1.0 targeted static adapter."""
from . import check_workflow
from ..limits import DEFAULT_MAX_NODES, DEFAULT_MAX_LINKS


def validate(value, max_nodes=DEFAULT_MAX_NODES, max_links=DEFAULT_MAX_LINKS):
    return check_workflow(value, max_nodes=max_nodes, max_links=max_links)
