"""Main function of the program."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import IO, TYPE_CHECKING

import mdformat
from griffe import GriffeLoader, Parser
from jinja2 import Environment, FileSystemLoader

from griffe2md import rendering

if TYPE_CHECKING:
    from griffe import Object


def _output(text: str, to: IO | str | None = None) -> None:
    if isinstance(to, str):
        with open(to, "w") as output:
            output.write(text)
    else:
        if to is None:
            to = sys.stdout
        to.write(text)


def prepare_context(obj: Object, config: dict | None = None) -> dict:
    """Prepare Jinja context.

    Parameters:
        obj: A Griffe object.
        config: The configuration options.

    Returns:
        The Jinja context.
    """
    config = dict(rendering.default_config, **(config or {}))
    if config["filters"]:
        config["filters"] = [
            (re.compile(filtr.lstrip("!")), filtr.startswith("!"))
            for filtr in config["filters"]
        ]

    heading_level = config["heading_level"]
    try:
        config["members_order"] = rendering.Order(config["members_order"])
    except ValueError as error:
        choices = "', '".join(item.value for item in rendering.Order)
        raise ValueError(
            f"Unknown members_order '{config['members_order']}', choose between '{choices}'.",
        ) from error

    summary = config["summary"]
    if summary is True:
        config["summary"] = {
            "attributes": True,
            "functions": True,
            "classes": True,
            "modules": True,
        }
    elif summary is False:
        config["summary"] = {
            "attributes": False,
            "functions": False,
            "classes": False,
            "modules": False,
        }
    else:
        config["summary"] = {
            "attributes": summary.get("attributes", False),
            "functions": summary.get("functions", False),
            "classes": summary.get("classes", False),
            "modules": summary.get("modules", False),
        }

    return {
        "config": config,
        obj.kind.value: obj,
        "heading_level": heading_level,
        "root": True,
    }


def prepare_env(env: Environment | None = None) -> Environment:
    """Prepare Jinja environment.

    Parameters:
        env: A Jinja environment.

    Returns:
        The Jinja environment.
    """
    env = env or Environment(
        autoescape=False,  # noqa: S701
        loader=FileSystemLoader([Path(__file__).parent / "templates"]),
        auto_reload=False,
    )
    env.filters["any"] = rendering.do_any
    env.filters["heading"] = rendering.do_heading
    env.filters["as_attributes_section"] = rendering.do_as_attributes_section
    env.filters["as_classes_section"] = rendering.do_as_classes_section
    env.filters["as_functions_section"] = rendering.do_as_functions_section
    env.filters["as_modules_section"] = rendering.do_as_modules_section
    env.filters["filter_objects"] = rendering.do_filter_objects
    env.filters["format_code"] = rendering.do_format_code
    env.filters["format_signature"] = rendering.do_format_signature
    env.filters["format_attribute"] = rendering.do_format_attribute
    env.filters["order_members"] = rendering.do_order_members
    env.filters["split_path"] = rendering.do_split_path
    # Use a more robust stash_crossref filter that doesn't cause encoding issues
    env.filters["stash_crossref"] = lambda ref, length: ref.replace(".", "")
    env.filters["from_private_package"] = rendering.from_private_package

    return env


def render_object_docs(obj: Object, config: dict | None = None) -> str:
    """Render docs for a given object.

    Parameters:
        obj: The Griffe object to render docs for.
        config: The rendering configuration.

    Returns:
        Markdown.
    """
    env = prepare_env()
    context = prepare_context(obj, config)
    rendered = env.get_template(f"{obj.kind.value}.md.jinja").render(**context)
    # Remove � characters from the output
    rendered = rendered.replace("�", "")
    return mdformat.text(rendered)


def render_package_docs(package: str, config: dict | None = None) -> str:
    """Render docs for a given package.

    Parameters:
        package: The package (name) to render docs for.
        config: The rendering configuration.

    Returns:
        Markdown.
    """
    config = config or dict(rendering.default_config)
    parser = config["docstring_style"] and Parser(config["docstring_style"])
    loader = GriffeLoader(docstring_parser=parser)
    module = loader.load(package)
    loader.resolve_aliases(external=True)
    return render_object_docs(module, config)  # type: ignore[arg-type]


def write_package_docs(
    package: str, config: dict | None = None, output: IO | str | None = None
) -> None:
    """Write docs for a given package to a file or stdout.

    Parameters:
        package: The package to render docs for.
        config: The rendering configuration.
        output: The file to write to.
    """
    _output(render_package_docs(package, config), to=output)
