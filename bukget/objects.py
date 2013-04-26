from urllib.request import urlopen
from urllib.parse import urlencode
from base64 import b64decode
from datetime import datetime
import json, bukget.api, bukget.exceptions

PLUGIN_URL = "http://api.bukget.org/3/plugins/bukkit/"
DATA = urlencode({"fields": "-logo_full,-server,-logo,-main,-versions.commands,\
                            -versions.permissions,-versions.changelog,\
                            -versions.status,-versions.dbo_version,-versions.slug"})


class Version(object):
    def __init__(self, json):
        self.status = json.get('status', None)
        if 'commands' in json:
            # TODO - But probably never will be done
            pass
        self.game_versions = json.get('game_versions', None)
        if 'changelog' in json:
            self.changelog = b64decode(json.get('changelog', None))
        self.filename = json.get('filename', None)
        self.hard_dependencies = json.get('hard_dependencies', None)
        self.download = json.get('download', None)
        self.number = json.get('version', None)
        self.link = json.get('link', None)
        if 'date' in json:
            self.timestamp = datetime.fromtimestamp(int(json.get('date', None)))
        if 'permissions' in json:
            # TODO - But probably never will be done
            pass
        self.type = json.get('type', None)
        self.slug = json.get('slug', None)
        self.soft_dependencies = json.get('soft_dependencies', None)
        self.md5 = json.get('md5', None)


class Plugin(object):
    def __init__(self, slug, fields, size):
        query = PLUGIN_URL + slug + "?" + urlencode({'fields': fields, 
                           'size': str(size)})
        response = urlopen(query)
        self.json_object = json.loads(response.readall().decode("utf-8"))
        
        if self.json_object is None or len(self.json_object) < 1:
            raise bukget.exceptions.NotFound("Could not find %s on BukGet!" % slug)
        
        self.website = self.json_object.get('website', None)
        self.devbukkit_page = self.json_object.get('dbo_page', None)
        self.description = self.json_object.get('description', None)
        self.full_logo = self.json_object.get('logo_full', None)
        self.name = self.json_object.get('plugin_name', None)
        self.server = self.json_object.get('server', None)
        self.authors = self.json_object.get('authors', None)
        self.logo = self.json_object.get('logo', None)
        self.main = self.json_object.get('main', None)
        self.slug = self.json_object.get('slug', None)
        self.categories = self.json_object.get('categories', None)
        self.stage = self.json_object.get('stage', None)

        if 'popularity' in self.json_object:
            self.popularity_monthly = self.json_object.get('popularity', None).get('monthly', None)
            self.popularity_weekly = self.json_object.get('popularity', None).get('weekly', None)
            self.popularity_daily = self.json_object.get('popularity', None).get('daily', None)

        if 'versions' in self.json_object:
            self.versions = {}
            for version_json in self.json_object.get('versions', None):
                version = Version(version_json)
                self.versions[version.number] = version
            for version in self.versions:
                if self.versions[version].type == "Release":
                    self.newest_version = self.versions[version]

    def get_hard_dependencies(self, hard_dependencies=True, version=None):
        if version is None:
            version = self.newest_version
        if hard_dependencies:
            return set([bukget.api.get_plugin(bukget.api.get_slug(dep)) for dep in version.hard_dependencies])
        else:
            return set([bukget.api.get_plugin(bukget.api.get_slug(dep)) for dep in version.soft_dependencies])
