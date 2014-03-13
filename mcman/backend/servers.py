import spacegdn

# TODO - Documentation!


def init(base, user_agent):
    spacegdn.BASE = base
    spacegdn.USER_AGENT = user_agent


def jars():
    result = spacegdn.jars()

    if type(result) is not list:
        return result

    return [jar['name'] for jar in result]


def channels(server):
    server = spacegdn.get_id(jar=server)
    result = spacegdn.channels(jar=server)

    if type(result) is not list:
        return result

    return [channel['name'] for channel in result]


def versions(server, channel, size):
    server = spacegdn.get_id(jar=server)
    channel = None
    if channel is not None:
        channel = spacegdn.get_id(jar=server, channel=channel)
    result = spacegdn.versions(jar=server, channel=channel)

    if type(result) is not list:
        return result

    # Sort and limit the results
    result = list(reversed(sorted([version['version'] for version
                                   in result])))
    if size >= 0:
        result = result[:min(size, len(result))]
    else:
        result = result[max(size, -len(result)):]

    return result


def builds(server, channel, version, size):
    server = spacegdn.get_id(jar=server)
    channel = None
    if channel is not None:
        channel = spacegdn.get_id(jar=server, channel=channel)
    if version is not None:
        version = spacegdn.get_id(jar=server, channel=channel, version=version)
    result = spacegdn.builds(jar=server, channel=channel, version=version)

    if type(result) is not list:
        return result

    # Sort and limit the results
    result = list(reversed(sorted([str(build['build']) for build
                                   in result])))
    if size >= 0:
        result = result[:min(size, len(result))]
    else:
        result = result[max(size, -len(result)):]

    return result


def get_builds(server, channel, version, build):
    server = spacegdn.get_id(jar=server)
    channel = None
    if channel is not None:
        channel = spacegdn.get_id(jar=server, channel=channel)
    version = None
    if version is not None:
        version = spacegdn.get_id(jar=server, channel=channel,
                                  version=version)
    build = None
    if build is not None:
        build = spacegdn.get_id(jar=server, channel=channel,
                                version=version,
                                build=build)

    return spacegdn.builds(jar=server, channel=channel,
                           version=version, build=build)


def build_by_checksum(checksum):
    result = spacegdn.builds(where='build.checksum.eq.{}'.format(checksum))
    if len(result) < 1:
        return None
    return result[0]


def get_roots(build):
    server = spacegdn.jars(build['jar_id'])[0]['name']
    channel = spacegdn.channels(build['jar_id'],
                                build['channel_id'])[0]['name']
    version = spacegdn.versions(build['jar_id'], build['channel_id'],
                                build['version_id'])[0]['version']
    build = build['build']

    return server, channel, version, build


def find_latest_build(builds):
    builds.sort(key=lambda build: build['build'], reverse=True)
    build = builds[0]

    channel = spacegdn.channels(channel=build['channel_id'])[0]['name']
    version = spacegdn.versions(version=build['version_id'])[0]['version']

    return channel, version, build
