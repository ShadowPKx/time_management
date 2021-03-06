#!/usr/local/bin/python3

import inspect
import os
import random
import sys

currentdir = os.path.dirname(os.path.abspath(
        inspect.getfile(inspect.currentframe())))
sys.path.insert(0, currentdir)
from _common.api import translation
from _common.api import headers
from _common.api import auth
from _common.api import db

if (random.randint(1, 3000) == 100):
    db.clearDatabaseGarbage()
headers.htmlPage(True, "login/index.py")

print("""<!DOCTYPE html>
<html lang='""" + auth.user_lang + """'>
<head>
    <meta charset="utf-8" />
    <title>""" + translation.getAppName(auth.user_lang) + """</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <meta name="description" content="Reminder web application" />
    <meta name="referrer" content="no-referrer" />
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="mobile-web-app-status-bar-style" content="default" />
    <meta name="mobile-web-app-title" content="Full Screen" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="default" />
    <meta name="apple-mobile-web-app-title" content="Full Screen" />
    <link rel="manifest" href="manifest.json" />
    <meta name="author" content="Arefev Leonid" />
    <link rel="icon" href="data:;base64,iVBORw0KGgo=" />
    <link href="_common/css/bootstrap.min.css" rel="stylesheet" />
    <link href="_common/css/custom.css" rel="stylesheet" />
</head>

<body>
    <div id="content" style="overflow: hidden; height:100%;">
        <div style="text-align:center;"><br />&nbsp;<br><img src="_common/img/loader.gif" /><br />&nbsp;&nbsp;Loading...</div>
    </div>

    <script type="text/javascript" src="_common/js/jquery.min.js"></script>
    <script type="text/javascript" src="_common/js/json2html.min.js"></script>
    <script type="text/javascript" src="_common/js/popper.min.js"></script>
    <script type="text/javascript" src="_common/js/bootstrap.min.js"></script>

    <script type="text/javascript" src="_common/js/feather.min.js"></script>
    <script type="text/javascript" src="_common/js/project_functions.js"></script>
    <script type="text/javascript" src="main/js/functions.js"></script>

    <script type="text/javascript">
        const translation_strings = """ + translation.get_array(auth.user_lang) + """;
        function getTranslations(){
            return translation_strings;
        }
        function init() {
            jth.setTranslationArray(getTranslations()); // optional
            jth.loadTemplatesArray( ["_common/html/templates.html", "main/html/navigation.html"], loadingCallback);
        }

        function loadingCallback() {
            buildWebUI();
        }
        init(); //Run it immediately after loading page
    </script>
</body>

</html>""")
