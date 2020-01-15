#!/usr/bin/env python3
import os
import pathlib
import shutil
import sys
import argparse


class AppGenerator(object):
    """
    Driving class for the SecureFlaskApp CLI
    """

    # directory containing templated app files
    __dir = pathlib.PurePath(__file__).parent / "files"

    def __init__(self, cmd_line_args):
        if cmd_line_args.output_directory:
            self.__path = pathlib.Path(cmd_line_args.output_directory, cmd_line_args.name)
            self.__path_provided = True
        else:
            self.__path = pathlib.Path(".", cmd_line_args.name)
            self.__path_provided = False
        self.__path_str = str(self.__path) if self.__path_provided else f"./{str(self.__path)}"

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
            os.path.join(self.__path, "docker-overrides"),
            os.path.join(self.__path, "docker"),
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
                out_compose.write("".join(compose_file.readlines()).format(port_number=self.__port, database_user=self.__database_user))
        with open(in_override, "r") as override_file:
            with open(str(self.__path / "SAMPLE.docker-compose.override.yml"), "w") as out_override:
                out_override.write("".join(override_file.readlines()).format(app_name=self.__name))
        with open(in_dockerfile, "r") as dockerfile:
            with open(str(self.__path / "docker" / "Dockerfile"), "w") as out_dockerfile:
                out_dockerfile.write("".join(dockerfile.readlines()))
        with open(str(self.__dir / "cli.dev.Dockerfile"), "r") as dockerfile_alt:
            with open(str(self.__path / "docker" / "dev.Dockerfile"), "w") as out_dockerfile_alt:
                out_dockerfile_alt.write("".join(dockerfile_alt.readlines()))
        for instance in ["dev", "test", "prod"]:
            with open(str(self.__dir / f"cli.{instance}.docker-compose.override.yml"), "r") as in_compose:
                with open(str(self.__path / "docker-overrides" / f"{instance}.docker-compose.override.yml"), "w") as out_compose:
                    if instance == "prod":
                        out_compose.write("".join(in_compose.readlines()).format(database_user=self.__database_user, app_name=self.__name))
                    else:
                        out_compose.write("".join(in_compose.readlines()).format(database_user=self.__database_user))


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
            if self.__asset_management:
                contents += "\nFlask-Assets"
            with open(str(self.__path / "requirements.txt"), "w") as out_requirements:
                out_requirements.write(contents)

    def __setup_env(self):
        rs_config = ""
        if self.__role_security:
            for line in ["security_schema=webappmgr", "security_role_table=app_role", "security_user_table=app_user", "security_user_role_table=app_user_app_role"]:
                rs_config += f"{line}\n"
        with open(str(self.__dir / "cli.SAMPLE.env"), "r") as in_env:
            sample_path = str(self.__path / "SAMPLE.env")
            with open(sample_path, "w") as out_env:
                out_env.write("".join(in_env.readlines()).format(cas_url=self.__cas_url, db_user=self.__database_user, app_name=self.__name) + rs_config)
            shutil.copyfile(sample_path, str(self.__path / ".env"))


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
        with open(str(self.__dir / "cli.main.css"), "r") as in_css:
            with open(str(self.__path / "app" / "static" / "css" / "main.css"), "w") as out_css:
                out_css.write("".join(in_css.readlines()))

    def __setup_images(self):
        for i in ["favicon.ico", "rowan_torch_logo_small.png"]:
            shutil.copyfile(
                str(self.__dir / f"cli.{i}"),
                str(self.__path / "app" / "static" / "images" / i)
            )
        
    def __setup_html(self):
        for temp in ["layout.html", "index.html"]:
            with open(str(self.__dir / f"cli.{temp}"), "r") as in_temp:
                with open(str(self.__path / "app" / "templates" / temp), "w") as out_temp:
                    out_temp.write("".join(in_temp.readlines()).format(app_name=self.__name))


    def __finished(self):
        
        print(f"\nYour app has been created at {self.__path_str}")
        print("Do the following steps to run your app:")
        print(f"\t1. cd {self.__path_str}")
        print(f"\t2. ./dba/setup.sh <password for database user>")
        print(f"\t3. sed -i \"\" 's/db_password=/db_password=<password for database user>/g' .env")
        print(f"\t4. docker-compose up --build\n")

        print("Things to remember:")
        print("\t- Submit a ticket to whitelist your application's PROD and TEST urls with CAS.")
        print("\t- If you are using GIT for version control, run:")
        print("\t\t1. git init")
        print("\t\t2. git remote add origin <remote url>")
        print("\t\t3. git add .")
        print("\t\t4. git commit -m \"init commit\"")
        print("\t\t5. git push\n")

        
    def init(self):
        self.__setup_directories()
        self.__setup_app_file()
        self.__setup_docker()
        self.__setup_ddl()
        self.__setup_requirements()
        self.__setup_env()
        self.__setup_readme()
        self.__setup_misc()
        self.__setup_images()
        self.__setup_html()
        self.__finished()


def flask_init_process_input(in_arg):
    processed_arg = []
    user_in = input(in_arg["help"])
    if not user_in and "default" in in_arg:
        user_in = in_arg["default"]
    if "required" in in_arg:
        valid = user_in.lower() not in (None, "")
        while not valid:
            print("Input is required.")
            user_in = input(in_arg["help"])
            valid = user_in.lower() not in (None, "")
        processed_arg.extend([f"--{in_arg['name']}", user_in])
    elif "flag" in in_arg:
        valid = user_in.lower() in ("y", "n")
        while not valid:
            print("Invalid option specified.")
            user_in = input(in_arg["help"])
            valid = user_in.lower() in ("y", "n")
        if user_in.lower() == "y":
            processed_arg.append(f"--{in_arg['name']}")
    elif "list" in in_arg:
        processed_arg.append(f"--{in_arg['name']}")
        user_in = user_in.strip()  
        split_up = user_in.split(" ")
        user_in = [] if not user_in else user_in
        processed_arg.extend(split_up if split_up else user_in)
    else:
        processed_arg.extend([f"--{in_arg['name']}", user_in])
    return dict(processed_arg=processed_arg, key=in_arg["name"], value=user_in)


def flask_init_prompt():
    print("\nInitialize a profpy-flask app.")
    out_args = []
    name_arg = flask_init_process_input(dict(name="name", help="Name of application (required): ", required=True))
    out_args.extend(name_arg["processed_arg"])
    for arg in [
        dict(name="port", help="Port to run the application on (required): ", required=True),
        dict(name="database-user", help="The database user for the application (required): ", required=True),
        dict(name="output-directory", help=f"The output directory (\"./{name_arg['value']}\"): "),
        dict(name="cas-url", help="The CAS url (https://login.rowan.edu): ", default="https://login.rowan.edu"),
        dict(name="database-objects", help="Database tables/views for the application to have access to (e.g. schema1.table1 schema2.table2): ", list=True),
        dict(name="requirements", help="Any additional requirements for requirements.txt: ", list=True),
        dict(name="role-security", help="Whether or not to use role-based security (Y/n): ", flag=True, default="y"),
        dict(name="asset-management", help="Whether or not to use flask-assets (Y/n): ", flag=True, default="y"),
        dict(name="force-create", help="Delete an existing application in the given directory with the same name (y/N): ", flag=True, default="n")
    ]:
        out_args.extend(flask_init_process_input(arg)["processed_arg"])
    return out_args

def flask_init_argparser():     
    parser = argparse.ArgumentParser(
        description="Initialize a profpy-flask app."
    )
    parser.add_argument("-n", "--name", required=True, type=str, help="The name of the application.")
    parser.add_argument("-f", "--force-create", action="store_true", help="If the project name already exists in the output directory, delete it before running this tool.")
    parser.add_argument("-p", "--port", required=True, type=int, help="The port that Docker will run this application on.")
    parser.add_argument("-rs", "--role-security", action="store_true", help="Whether or not to configure Spring-like, role-based security.")
    parser.add_argument("-c", "--cas-url", default="https://login.rowan.edu", required=True, type=str, help="The fully-qualified CAS url, (defaults to https://login.rowan.edu)"),
    parser.add_argument("-o", "--output-directory", type=str, help="Optional output directory (defaults to current directory)")
    parser.add_argument("-a", "--asset-management", action="store_true", help="Whether or not to set up integration with Flask-Assets")
    parser.add_argument("-dbu", "--database-user", type=str, required=True, help="The Oracle user that will be the backing database user for this application.")
    parser.add_argument("-dbo", "--database-objects", type=str, nargs="*", help="Any tables/views to allow your app to have access to. Must be fully qualified names (schema.table).")
    parser.add_argument("-rq", "--requirements", type=str, nargs="*", help="Any additional dependencies to have in requirements.txt (profpy is placed in there by default).")
    return parser


def flask_init(cmd_line_args):
    AppGenerator(cmd_line_args).init()
