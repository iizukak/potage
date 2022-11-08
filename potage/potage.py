import argparse
import os
import dataclasses
from pathlib import Path
from jinja2 import Template
import yaml
import importlib
from importlib.metadata import version
import importlib.resources
import pprint
from markdown import markdown
from datetime import date

CONFIG_FILE_NAME = "potage.yaml"
CSS_FILE_NAME = "potage.css"


@dataclasses.dataclass
class MarkDownFile:
    path: Path
    output_path: Path
    output_dir: Path
    created_at: str
    edited_at: str
    contents: str


def parse_command_line_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="potage: Minimal Static Site Generator."
    )
    parser.add_argument("--version", action="store_true", help="Show potage version.")
    args = parser.parse_args()
    return args


def print_version():
    v = version("potage")
    print("potage version: " + v)


def parse_config() -> dict:
    with open(CONFIG_FILE_NAME) as file:
        config = yaml.safe_load(file)
    print("load settings...")
    pprint.pprint(config)
    print()
    return config


def load_template() -> tuple[str, str, str]:
    # Load jinja2 template files.
    # index.html is a main page template of the site.
    # pages.html is a general page template.
    pkg = importlib.resources.files("potage")
    index_template_path = pkg / "template" / "index.html"
    page_template_path = pkg / "template" / "pages.html"
    css_path = pkg / "template" / CSS_FILE_NAME
    index_template = index_template_path.read_text()
    page_template = page_template_path.read_text()
    css = css_path.read_text()
    return index_template, page_template, css


def load_markdown_files(config: dict) -> list[MarkDownFile]:
    # Load .md files in input_dir, recursively.
    # Retuen a list of MarkDown instances.
    print("collecting target markdown files...")
    markdown_files = []
    input_paths = Path(config["input_dir"]).glob("**/*.md")
    for path in input_paths:
        print(path)
        output_dir = Path(config["output_dir"], *path.parts[1:-1])
        output_html_file_name = path.stem + ".html"
        output_path = Path(output_dir, output_html_file_name)
        stat = os.stat(path)
        with open(path) as f:
            contents = f.read()
        markdown_file = MarkDownFile(
            path=path,
            output_path=output_path,
            output_dir=output_dir,
            created_at=stat.st_birthtime,
            edited_at=stat.st_mtime,
            contents=contents,
        )
        markdown_files.append(markdown_file)
    print()
    return markdown_files


def make_output_dirs(markdown_files: list[MarkDownFile]):
    # Make output directories recursively
    for markdown_file in markdown_files:
        os.makedirs(markdown_file.output_dir, exist_ok=True)


def make_time_str(timestamp: str, config: dict) -> str:
    d = date.fromtimestamp(int(timestamp))
    return d.strftime(config["date_format"])


def convert_index(markdown_file: MarkDownFile, config: dict, template: str):
    # Convert index.md's MarkDown instance to index.html.
    markdown_html = markdown(markdown_file.contents)
    created_at = make_time_str(markdown_file.created_at, config)
    updated_at = make_time_str(markdown_file.edited_at, config)
    year = date.today().year
    template = Template(source=template)
    converted_html = template.render(
        contents=markdown_html,
        config=config,
        created_at=created_at,
        updated_at=updated_at,
        year=year,
    )
    print(converted_html)
    with open(markdown_file.output_path, "w") as f:
        f.write(converted_html)


def convert_page(markdown_file: MarkDownFile, config: dict, template: str):
    # Convert a MarkDown instance into page.html
    pass


def convert(
    markdown_files: list[MarkDownFile], config: dict, templates: tuple[str, str]
):
    for markdown_file in markdown_files:
        print(markdown_file.path)
        if markdown_file.path == Path(config["input_dir"], "index.md"):
            print("This is the index file")
            convert_index(markdown_file, config, templates[0])
        else:
            print("This is not index file")
            convert_page(markdown_file, config, templates[1])


def write_css(css: str, config: dict):
    output_path = Path(config["output_dir"]) / CSS_FILE_NAME
    with open(output_path, "w") as f:
        f.write(css)


def main():
    args = parse_command_line_args()
    if args.version == True:
        print_version()
    else:
        config = parse_config()
        index_template, page_template, css = load_template()
        markdown_files = load_markdown_files(config)
        make_output_dirs(markdown_files)
        convert(markdown_files, config, (index_template, page_template))
        write_css(css, config)
