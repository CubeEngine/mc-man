from urllib.request import urlopen
from urllib.parse import urlencode
from base64 import b64decode
from datetime import datetime
import json, bukget.api

PLUGIN_URL = "http://api.bukget.org/3/plugins/bukkit/"
DATA = urlencode({"fields": "-logo_full,-server,-logo,-main,-versions.commands,\
                            -versions.permissions,-versions.changelog,\
                            -versions.status,-versions.dbo_version,-versions.slug"})


class Version(object):
    def __init__(self, json):
        self.status = json['status']
        if 'commands' in json:
            # TODO - But probably never will be done
            pass
        self.game_versions = json['game_versions']
        if 'changelog' in json:
            self.changelog = b64decode(json['changelog'])
        self.filename = json['filename']
        self.hard_dependencies = json['hard_dependencies']
        self.download = json['download']
        self.number = json['version']
        self.link = json['link']
        if 'date' in json:
            self.timestamp = datetime.fromtimestamp(int(json['date']))
        if 'permissions' in json:
            # TODO - But probably never will be done
            pass
        self.type = json['type']
        self.slug = json['slug']
        self.soft_dependencies = json['soft_dependencies']
        self.md5 = json['md5']


class Plugin(object):
    def __init__(self, slug, fields, size):
        response = urlopen(PLUGIN_URL + slug, urlencode({'fields': fields, 'size': str(size)}))
        self.json_object = json.loads(response.readall().decode("utf-8"))

        self.website = self.json_object['website']
        self.devbukkit_page = self.json_object['dbo_page']
        self.description = self.json_object['description']
        self.full_logo = self.json_object['logo_full']
        self.name = self.json_object['plugin_name']
        self.server = self.json_object['server']
        self.authors = self.json_object['authors']
        self.logo = self.json_object['logo']
        self.main = self.json_object['main']
        self.slug = self.json_object['slug']
        self.categories = self.json_object['categories']
        self.stage = self.json_object['stage']

        if 'popularity' in self.json_object:
            self.popularity_monthly = self.json_object['popularity']['monthly']
            self.popularity_weekly = self.json_object['popularity']['weekly']
            self.popularity_daily = self.json_object['popularity']['daily']

        if 'versions' in self.json_object:
            self.versions = {}
            for version_json in self.json_object['versions']:
                version = Version(version_json)
                self.versions[version.number] = version
            for version in self.versions:
                if version.type == "Release":
                    self.newest_version = version

    def get_hard_dependencies(self, hard_dependencies=True, version=None):
        if version is None:
            version = self.newest_version
        if hard_dependencies:
            return set([bukget.api.get_plugin(bukget.api.get_slug(dep)) for dep in version.hard_dependencies])
        else:
            return set([bukget.api.get_plugin(bukget.api.get_slug(dep)) for dep in version.soft_dependencies])
