
"""
Build Nick's prefered default project starting point for new websites. The 
project will precompile sass files for css, and use bottle as the web 
framework. It will be geared towards deployment on a cherrypy server using a 
nginx reverse proxy.

Requirements:
    - Python 3.x
    - CoffeeScript
    - Sass
    - Git
    - Inkscape
    - Imagemagick

Copyright (c) 2015, Nick Balboni.
License: BSD (see LICENSE for details)
"""



################################################################################
##### Command Line Interface ###################################################
################################################################################

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os

parser = ArgumentParser(
    formatter_class=ArgumentDefaultsHelpFormatter,
    description=__doc__ )
parser.add_argument("name", 
    type=str,
    metavar="NAME",
    nargs="?",
    default="untitled",
    help="the name of the project for the new website." )
parser.add_argument("-p", "--path", 
    type=str,
    default=os.getcwd(),
    help="the path to the desired location of the new project." )
parser.add_argument("-f", "--favicon", 
    type=str,
    help="location of image file to be used as the favicon for the project. "
    "If an absolute path is not given, location will be assumed to be relative "
    "to the location of this script. It is required to provide a square svg "
    "file for use here." )
parser.add_argument("-r", "--resources", 
    type=str,
    nargs='+',
    help="locations of any additional resources to be added to the project. If "
    "an absolute path is not given, location will be assumed to be relative to "
    "the location of this script." )
args = parser.parse_args()



################################################################################
##### Overrides ################################################################
################################################################################

OVERRIDES = """\
from string import Template
from re import compile

class TemplateWrapper():

    def __init__(self, cls):
        PYTHON_LL = 80
        HTML_LL   = 120

        self.cls = cls
        self.headers = [
            (   # Primary python file header template
                compile(r'\$ph{(.*?)}'),
                lambda x: "\\n\\n{1}\\n##### {0} {2}\\n{1}\\n".format(
                    x.upper(), '#'*PYTHON_LL, '#'*(PYTHON_LL-len(x)-7) )
            ),
            (   # Secondary python file header template
                compile(r'\$sh{(.*?)}'),
                lambda x: "\\n### {0} {1}".format(
                    x, '#'*(PYTHON_LL-len(x)-5) )
            ),
            (   # HTML file header template
                compile(r'\$wh{(.*?)}'),
                lambda x: "<!-- ***** {0} {1} -->".format(
                    x, '*'*(HTML_LL-len(x)-16) )
            )
        ]
        
    def __call__(self, template):
        for header in self.headers:
            ptn, tpl = header
            for match in ptn.finditer(template):
                replacements = ( match.group(0), tpl(match.group(1)) )
                template = template.replace(*replacements)
        template_obj = self.cls(template)
        template_obj.populate = self.populate
        return template_obj

    @staticmethod
    def populate(template, filepath, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, list):
                kwargs[key] = "\\n".join(
                    [ t[0].safe_substitute(**t[1]) for t in value ]
                )
        try:
            with open(filepath, 'w') as f:
                f.write(template.safe_substitute(**kwargs))
        except Exception as exception:
            raise exception

Template = TemplateWrapper(Template)


from subprocess import Popen, call, DEVNULL, STDOUT, PIPE
from sys import executable

def sPopen(*args):
    command, shell = list(args), True
    if command[0] == 'python': 
        command[0] = executable
        shell = False
    if os.name == 'nt':
        from subprocess import CREATE_NEW_CONSOLE
        Popen( command, shell=shell, creationflags=CREATE_NEW_CONSOLE )
    else:
        Popen( command, shell=shell )

def sCall(*args):
    command, shell = list(args), True
    if command[0] == 'python': 
        command[0] = executable
        shell = False
    call( command, shell=shell, stdout=DEVNULL, stderr=STDOUT )
"""

with open('overrides.py', 'w') as f:
    f.write(OVERRIDES)

from overrides import sPopen, sCall
from overrides import TemplateWrapper
from string import Template

Template = TemplateWrapper(Template)



################################################################################
##### Templates ################################################################
################################################################################

BASE_PARTIAL_SASS_TEMPLATE = Template("""\
body.main {
    @include fixpos(0);
    margin: 0;
    padding: 0;
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
    font-family: $main-font-stack; }
""" )


BASE_MODULE_SASS_TEMPLATE = Template("""\
$main-font-stack: 'Lato', sans-serif;

""" )


STYLES_SASS_TEMPLATE = Template("""\
@import "all";

""" )


UPDATE_SASS_TEMPLATE = Template("""\
from urllib.request import urlopen
from shutil import copyfileobj
import os


RESOURCES = (
[ 
    { 
        "name": "_flex-box_mixins.scss",
        "url":( "https://raw.githubusercontent.com/"
                "mastastealth/sass-flex-mixin/master/_flexbox.scss" ) 
    },

    { 
        "name": "_media-query_mixins.scss",
        "url":( "https://raw.githubusercontent.com/"
                "paranoida/sass-mediaqueries/master/_media-queries.scss" )
    },

    { 
        "name": "_general_mixins.scss",
        "url":( "https://raw.githubusercontent.com/"
                "SwankSwashbucklers/some-sassy-mixins/master/mixins.scss" ) 
    } 
]
)

def populate_resource(resource_name, resource_url):
    try:
        with urlopen(resource_url) as response, \\
                open(resource_name, 'wb') as f:
            copyfileobj(response, f)
        print("Successfully populated '{}'".format(resource_name))
    except Exception as e:
        message = "Could not populate resource" \\
            if not (os.path.isfile(resource_name)) \\
            else "Unable to update resource"
        print("{}: {}\\n  from url: {}\\nException: {}".format(
            message, resource_name, resource_url, e ) )


print("Updating external sass resources")
for resource in RESOURCES:
    populate_resource(resource['name'], resource['url'])
""" )



HEAD_TEMPLATE = Template("""\
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, 
    maximum-scale=1.0, user-scalable=no">

    <title>{{title}}</title>

    <meta name="description" content="{{description}}">
    <meta name="author" content="Nick Balboni">
    <meta name="favicon_elements">
    <meta name="open_graph">
    <meta name="stylesheets">
</head>
""" )


INDEX_TEMPLATE = Template("""\
<!DOCTYPE html>
<html lang="en">
% include('~head.tpl', title='$title', description='$description')
    <body>
    </body>
</html>
""" )


ROUTES_TEMPLATE = Template("""\
@route('/', method='POST')
def api():
    if request.POST.get("v") == 'vendetta': 
        return \"""\\
Evey:  Who are you?
   V:  Who? Who is but the form following the function of what, and what 
       I am is a man in a mask.
Evey:  Well I can see that.
   V:  Of course you can. I'm not questioning your powers of observation; 
       I'm merely remarking upon the paradox of asking a masked man who 
       he is.
Evey:  Oh. Right.
   V:  But on this most auspicious of nights, permit me then, in lieu of 
       the more commonplace sobriquet, to suggest the character of this 
       dramatis persona.
   V:  Voila! In view, a humble vaudevillian veteran cast vicariously as 
       both victim and villain by the vicissitudes of Fate. This visage, 
       no mere veneer of vanity, is a vestige of the vox populi, now 
       vacant, vanished. However, this valourous visitation of a bygone 
       vexation stands vivified and has vowed to vanquish these venal and 
       virulent vermin vanguarding vice and vouchsafing the violently 
       vicious and voracious violation of volition! The only verdict is 
       vengeance; a vendetta held as a votive, not in vain, for the value 
       and veracity of such shall one day vindicate the vigilant and the 
       virtuous. Verily, this vichyssoise of verbiage veers most verbose, 
       so let me simply add that it's my very good honour to meet you and 
       you may call me V.
\"""
    return load_root()
""" )


ROBOTS_TEMPLATE = Template("""\
User-agent: *
Disallow:
""" )



################################################################################
##### Script Body ##############################################################
################################################################################

import sys 
import time
import urllib.request, shutil
import errno, re

SCRIPT_DIR     = os.getcwd()
PROJECT_DIR    = os.path.join(os.path.abspath(args.path), args.name)
RE_USER_ACCEPT = re.compile(r'y(?:es|up|eah)?$', re.IGNORECASE)
RE_USER_DENY   = re.compile(r'n(?:o|ope|ada)?$', re.IGNORECASE)


def fatal_exception(exception, message="", cleanup=True):
    print("*******SCRIPT FAILED*******")
    if (message): print(message)
    print("Exception: ", exception)
    os.chdir(args.path)
    os.remove("overrides.py")
    sys.exit(1)

    if (cleanup):
        try:
            shutil.rmtree(args.name)
        except Exception as e:
            print(e)
    sys.exit(1)


def non_fatal_exception(exception, message, *args):
    while 1:
        response = input(message)
        if (RE_USER_ACCEPT.match(response)):
            return
        if (RE_USER_DENY.match(response)):
            fatal_exception(exception, "Script canceled by user", *args)




print("Creating folder for new project")
try:
    args.path = os.path.abspath(args.path)
    os.chdir(args.path)
except OSError as exception:
    fatal_exception(exception, "Invalid path provided", False)

try:
    os.makedirs(args.name)
except OSError as exception:
    # TODO: add ability to update an already existing project
    if (exception.errno == errno.EEXIST): 
        shutil.rmtree(args.name)
        os.makedirs(args.name)
        #non_fatal_exception(exception,
        #    "Folder already exists at \'{}\' ".format(os.getcwd())    + 
        #    "with the desired project name. Do you wish to proceed? " +
        #    "(script will use this folder for the project)? [yes/no]", False)
    else:
        fatal_exception(exception, "Could not create project folder", False)



print("Building out directory structure for the project")
try:
    os.chdir(PROJECT_DIR)
    os.makedirs("dev/ts")
    os.makedirs("dev/py")
    os.makedirs("dev/sass/modules")
    os.makedirs("dev/sass/partials")
    os.makedirs("dev/sass/vendor")
    os.makedirs("dev/views")
    os.makedirs("res/font")
    os.makedirs("res/img")
    os.makedirs("res/static")
except OSError as exception:
    fatal_exception(exception, "Could not build project directory structure")



print("Setting up python resources")
try:
    os.chdir(os.path.join(PROJECT_DIR, 'dev/py'))
    Template.populate(ROUTES_TEMPLATE, 'routes.py')
except Exception as exception:
    fatal_exception(exception, "Could not create routes file")



print("Creating sass scripts and pulling in resources")
try:
    os.chdir(os.path.join(PROJECT_DIR, 'dev/sass'))
    Template.populate(STYLES_SASS_TEMPLATE, 'styles.scss')
    os.chdir('partials')
    Template.populate(BASE_PARTIAL_SASS_TEMPLATE, '_base.scss')
    os.chdir('../modules')
    Template.populate(BASE_MODULE_SASS_TEMPLATE, '_base.scss')
except Exception as exception:
    fatal_exception(exception, "Could not build sass project")

try:
    os.chdir(os.path.join(PROJECT_DIR, 'dev/sass/vendor'))
    Template.populate(UPDATE_SASS_TEMPLATE, 'update.py')
    sCall( 'python', 'update.py' ) # wait for update to finish
    # so that sass can properly be compiled when site is built
except Exception as exception:
    fatal_exception(exception, "Could not pull in external sass resources")



print("Creating default views for bottle project")
try:
    os.chdir(os.path.join(PROJECT_DIR, 'dev/views'))
    Template.populate(HEAD_TEMPLATE, '~head.tpl')
    Template.populate(INDEX_TEMPLATE, 'index.tpl', 
        title=args.name, 
        description="Welcome to {}!".format(args.name) )
except Exception as exception:
    fatal_exception(exception, "Could not build default views")



print("Populating project resources")
try: # TODO: add checking if image doesn't meet requirements
    os.chdir(os.path.join(PROJECT_DIR, 'res'))
    if not args.favicon is None: # TODO: raise warning instead
        if not os.path.isabs(args.favicon):
            args.favicon = os.path.join(SCRIPT_DIR, args.favicon)
        if os.path.isdir(args.favicon):
            args.favicon = os.path.join(args.favicon, "favicon.svg")
        if os.path.splitext(args.favicon)[-1].lower() != '.svg':
            raise Exception("Given image file does not meet requirements")
        shutil.copy(args.favicon, "favicon.svg")
except Exception as exception:
    non_fatal_exception(exception, 
        "Unable to import favicon image. Do you wish to proceed? [yes/no]")

try:
    os.chdir(os.path.join(PROJECT_DIR, 'res'))
    if not args.resources is None: # TODO: raise warning instead
        resources = []
        for resource_path in args.resources:
            if not os.path.isabs(resource_path):
                resource_path = os.path.join(SCRIPT_DIR, resource_path)
            if os.path.isfile(resource_path):
                resource.append(resource_path)
            elif os.path.isdir(resource_path):
                for root, dirs, files in os.walk(resource_path):
                    for filename in files:
                        resources.append(os.path.join(root, filename))
        for resource in resources: # TODO: could use some improvement
            name = os.path.split(resource)[-1]
            ext = os.path.splitext(resource)[-1].lower()
            if ext == '.svg':
                font_posibilities = [
                                        resource[:-4] + '.eot', 
                                        resource[:-4] + '.ttf', 
                                        resource[:-4] + '.woff'
                                    ]
                if any(res in resources for res in font_posibilities): 
                    # font file with same name means this one is a font too
                    shutil.copy(resource, os.path.join('font', name))
                else:
                    shutil.copy(resource, os.path.join('img', name))
            elif ext in ['.png', '.jpg', '.jpeg', '.gif']:
                shutil.copy(resource, os.path.join('img', name))
            elif ext in ['.eot', '.ttf', '.woff']:
                shutil.copy(resource, os.path.join('font', name))
            else:
                shutil.copy(resource, os.path.join('static', name))
except Exception as exception:
    fatal_exception(exception, "Could not import project resources")

try:
    os.chdir(os.path.join(PROJECT_DIR, 'res/static'))
    if not os.path.isfile('robots.txt'): #user may have imported a robots.txt
        Template.populate(ROBOTS_TEMPLATE, 'robots.txt')
except Exception as exception:
    fatal_exception(exception, "Could not create default robots.txt")



print("Generating website in temporary directory")
try:
    os.chdir(PROJECT_DIR)
    shutil.copy(os.path.join(SCRIPT_DIR, 'build.py'), 'build.py')
    sPopen('python', 'build.py', '-d')
except Exception as exception:
    fatal_exception(exception, "Unable to generate website")


os.chdir(args.path)
os.remove("overrides.py")
