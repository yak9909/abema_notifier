import discord
import json
import abemagetter
import re
import requests
import os
import asyncio
import datetime
import yt_dlp


client = discord.Client(intents=discord.Intents.all())
with open('config.json', mode='r+', encoding='utf-8') as f:
    config = json.load(f)


def check_episode(checklist, anime):
    new_anime = []
    changed_anime = []
    
    if checklist is not None:
        for a in anime.episodes:
            ep = checklist.get('episodes').get(a.url)
            
            if ep is None:
                new_anime.append(a)
            else:
                if ep.get('free') is not a.free:
                    changed_anime.append(a)
            
            checklist["episodes"][a.url] = {
                "title": a.title,
                "thumbnail_url": a.thumbnail_url,
                "free": a.free
            }
    
    return {
        "checklist": checklist,
        "anime": {"new": new_anime, "changed": changed_anime}
    }


def checklist_update(anime):
    ret = {}

    with open('abema.json', mode='r+', encoding='utf-8') as f:
        checklist = json.load(f)
        
        checklisted = None
        
        # checklistを回す
        for i,a in enumerate(checklist.get('checklist')):
            # checklistに登録されているアニメのURLを取得し、変数 anime_url に代入 | is not Noneは保険
            if (anime_url := a.get('url')) is not None:
                # 既に登録されていたら
                if anime_url == anime.url:
                    ret = check_episode(a, anime)
                    checklist["checklist"][i] = ret["checklist"]
    
    # checklistに未登録のアニメだった場合
    if not ret:
        ret = {"anime": {"new": [x for x in anime.episodes], "changed": []}}
        
        # アニメをchecklistに登録する
        checklist["checklist"].append(
            {
                "url": anime.url,
                "episodes": {
                    x.url: {
                        "title": x.title,
                        "thumbnail_url": x.thumbnail_url,
                        "free": x.free
                    } for x in anime.episodes
                }
            }
        )
    
    # abema.json のアップデート
    with open('abema.json', mode='w', encoding='utf-8') as f:
        json.dump(checklist, f, ensure_ascii=False, indent=4)
    
    return ret


async def get_anime_channel(forum, anime):
    target = discord.utils.get(forum.threads, name=anime.title)
    if target is None:
        target = await forum.create_thread(name=anime.title, content=f'`{anime.title}` のエピソード情報を送信していきます')
        target = target[0]
    
    return target


async def check_anime(download=False):
    anime_list = json.load(open('abema_check.json', mode='r+', encoding='utf-8'))["check"]
    for url in anime_list:
        print(f'checking {url} ...')
        anime = abemagetter.Anime(url)
        ret = checklist_update(anime)
        
        download_queue = [x for x in ret.get('anime').get('new', []) if x.free]
        download_queue += [x for x in ret.get('anime').get('changed', []) if x.free]
        
        forum = await client.fetch_channel(config["forum_channelId"])
        target = await get_anime_channel(forum, anime)
        
        new_anime = ret.get('anime').get('new', [])
        changed_anime = ret.get('anime').get('changed', [])
        
        for a in new_anime:
            embed = discord.Embed(title='新しいエピソードが出ています！', description=f'[{a.title}]({a.url})')
            embed.set_author(name=anime.title, url=anime.url)
            embed.set_footer(text='無料で視聴できます' if a.free else 'プレミアム限定')
            embed.set_thumbnail(url=a.thumbnail_url)
            
            await target.send(embed=embed)
        
        if changed_anime:
            free = [x for x in changed_anime if x.free]
            premium = [x for x in changed_anime if not x.free]
            
            if free:
                episodes = '\n'.join([f'・[{x.title}]({x.url})' for x in free])
                embed = discord.Embed(title='以下のエピソードが現在無料配信中です！', description=episodes)
                embed.set_author(name=anime.title, url=anime.url)
                await target.send(embed=embed)

            if premium:
                episodes = '\n'.join([f'・[{x.title}]({x.url})' for x in premium])
                embed = discord.Embed(title='以下のエピソードの無料配信が終了しました…', description=episodes)
                embed.set_author(name=anime.title, url=anime.url)
                await target.send(embed=embed)
            
        for q in download_queue:            
            if download:
                download_anime(q)
        
    print('finish checking')
    print()


def download_anime(anime):
    if not os.path.exists(anime.anime.title):
        os.mkdir(anime.anime.title)

    ydl_opts = {
        "format": "2400",
        "outtmpl": f"{anime.anime.title}/%(title)s.%(ext)s"
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(anime.url, download=True)


@client.event
async def on_ready():
    print('bot ready!')
    checked = True
    await check_anime()
    
    while True:
        # 毎朝7時に送信
        if datetime.datetime.now().hour == 7:
            if not checked:
                checked = True
                await check_anime()
        else:
            checked = False
        await asyncio.sleep(30)


@client.event
async def on_message(message):
    if message.content.startswith('y!check '):
        url = message.content.split()[1]
    
        if not re.match(r'^https://abema.tv/video/title/.*', url):
            await message.reply('ABEMA TVのアニメURLを入力してください！')
            return
        
        if requests.get(url).status_code == 404:
            await message.reply('アニメが存在しないようです。URLが正しいかご確認ください！')
            return
        

client.run(config["token"])
