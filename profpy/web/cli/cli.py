#!/usr/bin/env python3
import functools
import os
import pathlib
import shutil
from argparse import Namespace, ArgumentParser


class AppArgNamespace(Namespace):
    def __init__(self):
        super().__init__()
        self.name = None
        self.role_security = None
        self.port = None
        self.cas_url = None
        self.output_directory = None
        self.asset_management = None
        self.database_user = None
        self.database_objects = []
        self.requirements = []


class AppGenerator(object):
    """
    Driving class for the SecureFlaskApp CLI
    """

    # directory containing templated app files
    __dir = pathlib.PurePath(__file__).parent / "files"

    def __init__(self, cmd_line_args):
        if cmd_line_args.output_directory:
            self.__path = pathlib.Path(cmd_line_args.output_directory, cmd_line_args.name)
        else:
            self.__path = pathlib.Path(".", cmd_line_args.name)

        if os.path.exists(self.__path):
            if cmd_line_args.force_create:
                shutil.rmtree(self.__path)
            else:
                raise IOError("Project already exists.")


        self.__name = cmd_line_args.name
        self.__role_security = cmd_line_args.role_security if cmd_line_args.role_security else False
        self.__port = cmd_line_args.port
        self.__cas_url = cmd_line_args.cas_url
        self.__asset_management = cmd_line_args.asset_management if cmd_line_args.asset_management else False
        self.__database_user = cmd_line_args.database_user
        
        if cmd_line_args.requirements:
            self.__requirements = cmd_line_args.requirements
        else:
            self.__requirements = []

        if cmd_line_args.database_objects:
            self.__tables = cmd_line_args.database_objects
        else:
            self.__tables = []
    

    def __setup_directories(self):
        directories = [
            self.__path,
            os.path.join(self.__path, "app"),
            os.path.join(self.__path, "app", "utils"),
            os.path.join(self.__path, "app", "templates"),
            os.path.join(self.__path, "app", "static"),
            os.path.join(self.__path, "app", "static", "images"),
            os.path.join(self.__path, "app", "static", "js"), 
            os.path.join(self.__path, "app", "static", "css"),
            os.path.join(self.__path, "dba")
        ]
        for d in directories:
            os.mkdir(d)

    def __setup_docker(self):
        in_compose = str(self.__dir / "cli.docker-compose.yml")
        in_override = str(self.__dir / "cli.SAMPLE.docker-compose.override.yml")
        in_dockerfile = str(self.__dir / "cli.Dockerfile")
        with open(in_compose, "r") as compose_file:
            with open(str(self.__path / "docker-compose.yml"), "w") as out_compose:
                out_compose.write("".join(compose_file.readlines()).format(port_number=self.__port))
        with open(in_override, "r") as override_file:
            with open(str(self.__path / "SAMPLE.docker-compose.override.yml"), "w") as out_override:
                out_override.write("".join(override_file.readlines()).format(app_name=self.__name))
        with open(in_dockerfile, "r") as dockerfile:
            with open(str(self.__path / "Dockerfile"), "w") as out_dockerfile:
                out_dockerfile.write("".join(dockerfile.readlines()))

    def __setup_app_file(self):
        in_path = str(self.__dir / "cli.main.py")
        out_path = str(self.__path / "app" / "main.py")
        asset_config = ""
        asset_import = ""
        pathlib.Path(str(self.__path / "app" / "utils" / "__init__.py")).touch()
        with open(in_path, "r") as sample_file:
            contents = "".join(sample_file.readlines())
            with open(out_path, "w") as output:
                if self.__asset_management:
                    pathlib.Path(str(self.__path / "app" / "static" / "js" / "site.js")).touch()
                    pathlib.Path(str(self.__path / "app" / "static" / "css" / "site.css")).touch()
                    asset_import = "from flask_assets import Environment, Bundle"
                    with open(str(self.__dir / "cli.asset_config.txt"), "r") as asset_config_txt:
                        asset_config = "".join(asset_config_txt.readlines()).format(app_name=self.__name)
                output.write(
                    contents.format(asset_config=asset_config, asset_import=asset_import, app_name=self.__name, tables=str(self.__tables))
                )
    
    def __setup_ddl(self):
        additional_grants = ""
        for t in self.__tables:
            additional_grants += f"grant select on {t} to {self.__database_user};\n"
        if self.__role_security:
            for t in ["app_user", "app_role", "app_user_app_role"]:
                additional_grants += f"grant select on webappmgr.{t} to {self.__database_user};\n"
        with open(str(self.__dir / "cli.db_user.ddl.sql"), "r") as user_file:
            with open(str(self.__path / "dba" / f"{self.__database_user}.ddl.sql"), "w") as out_user_file:
                out_user_file.write("".join(user_file.readlines()).format(additional_grants=additional_grants, database_user=self.__database_user))
        with open(str(self.__dir / "cli.setup.sh"), "r") as in_setup:
            with open(str(self.__path / "dba" / "setup.sh"), "w") as out_setup:
                out_setup.write("".join(in_setup.readlines()).format(database_user=self.__database_user))

    def __setup_requirements(self):
        with open(str(self.__dir / "cli.requirements.txt"), "r") as in_requirements:
            contents = "".join(in_requirements.readlines())
            for r in self.__requirements:
                contents += f"\n{r}"
            with open(str(self.__path / "requirements.txt"), "w") as out_requirements:
                out_requirements.write(contents)


    def __setup_env(self):
        rs_config = ""
        if self.__role_security:
            for line in ["security_schema=webappmgr", "security_role_table=app_role", "security_user_table=app_user", "security_user_role_table=app_user_app_role"]:
                rs_config += f"{line}\n"
        with open(str(self.__dir / "cli.SAMPLE.env"), "r") as in_env:
            with open(str(self.__path / "SAMPLE.env"), "w") as out_env:
                out_env.write("".join(in_env.readlines()).format(cas_url=self.__cas_url, db_user=self.__database_user) + rs_config)


    def __setup_readme(self):
        with open(str(self.__dir / "cli.README.md"), "r") as in_readme:
            with open(str(self.__path / "README.md"), "w") as out_readme:
                out_readme.write("".join(in_readme.readlines()).format(app_name=self.__name))


    def __setup_misc(self):
        with open(str(self.__dir / "cli.gitignore"), "r") as in_gi:
            with open(str(self.__path / ".gitignore"), "w") as out_gi:
                out_gi.writelines(in_gi.readlines())
        with open(str(self.__dir / "cli.LICENSE"), "r") as in_license:
            with open(str(self.__path / "LICENSE"), "w") as out_license:
                out_license.writelines(in_license.readlines())


    def init(self):
        self.__setup_directories()
        self.__setup_app_file()
        self.__setup_docker()
        self.__setup_ddl()
        self.__setup_requirements()
        self.__setup_env()
        self.__setup_readme()
        self.__setup_misc()



def with_cmd_line_args(f):
    @functools.wraps(f)
    def with_cmd_line_args_(*args, **kwargs):
        ap = ArgumentParser(description="Initialize a web application that utilizes the SecuredFlaskApp class and Docker.")
        ap.add_argument("-n", "--name", required=True, type=str, help="The name of the application.")
        ap.add_argument("-f", "--force-create", action="store_true", help="If the project name already exists in the output directory, delete it before running this tool.")
        ap.add_argument("-p", "--port", required=True, type=int, help="The port that Docker will run this application on.")
        ap.add_argument("-rs", "--role-security", action="store_true", help="Whether or not to configure Spring-like, role-based security.")
        ap.add_argument("-c", "--cas-url", required=True, type=str, help="The fully-qualified CAS url, e.g. https://login.rowan.edu")
        ap.add_argument("-d", "--output-directory", type=str, help="The directory to place this application, defaults to the directory where this script is being run.")
        ap.add_argument("-a", "--asset-management", action="store_true", help="Whether or not to set up integration with Flask-Assets")
        ap.add_argument("-dbu", "--database-user", type=str, required=True, help="The Oracle user that will be the backing database user for this application.")
        ap.add_argument("-dbo", "--database-objects", type=str, nargs="*", help="Any tables/views to allow your app to have access to. Must be fully qualified names (schema.table).")
        ap.add_argument("-rq", "--requirements", type=str, nargs="*", help="Any additional dependencies to have in requirements.txt (profpy is placed in there by default).")
        return f(ap.parse_args(namespace=AppArgNamespace), *args, **kwargs)
    return with_cmd_line_args_


@with_cmd_line_args
def main(cmd_line):
    AppGenerator(cmd_line).init()


if __name__ == "__main__":
    main()
