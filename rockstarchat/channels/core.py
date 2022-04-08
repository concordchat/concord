import orjson
from flask import request
from ..database import Channel, Message, Guild, to_dict
from ..checks import validate_member
from ..flags import GuildPermissions
from ..errors import Forbidden, BadData, NotFound
from ..randoms import _id, get_bucket
from ..redis_manager import guild_event

def create_channel(guild_id):
    guild_id = int(guild_id)

    guild: Guild = Guild.objects(Guild.id == guild_id).allow_filtering().first()

    if guild == None:
        raise NotFound()

    member, me = validate_member(str(request.headers.get('Authorization', '1')), guild_id)
    me = to_dict(me)
    me.pop('email')
    me.pop('password')
    me.pop('settings')
    me.pop('session_ids')

    permissions = None

    if member.roles == []:
        permissions = guild.permissions
    else:
        id = member.roles[0]

        for role in list(guild.roles):
            if role.id == id:
                permissions = role.permissions
                break

    assert permissions is not None
    
    calc = GuildPermissions(permissions)

    if not calc.manage_channels and member.id != guild.owner_id and not calc.administator:
        raise Forbidden()
    
    data: dict = request.get_json(True)

    slowmode = 0

    if data.get('slowmode_timeout'):
        if int(data.get('slowmode_timeout')) > 21600 or data.get('slowmode') < 0:
            raise BadData()
        else:
            slowmode = round(int(data.pop('slowmode_timeout')))
    
    if data.get('parent_id'):
        pid = int(data.pop('parent_id'))
    else:
        pid = None

    kwargs = {
        'id': _id(),
        'guild_id': guild_id,
        'name': str(data['name'])[:30].lower(),
        'topic': str(data.get('topic', ''))[:1024],
        'slowmode_timeout': slowmode,
        'type': int(data.get('type', 1)),
        'parent_id': pid
    }

    channel: Channel = Channel.create(**kwargs)
    d = to_dict(channel)

    d.pop('empty_buckets')

    guild_event('CHANNEL_CREATE', d=d)

    return orjson.dumps(d)
