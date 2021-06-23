import asyncio
import os
import requests
from pprint import pprint
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from urllib.request import urlopen
import sys
import json
import argparse

import discord
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

client = discord.Client()


@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name == '쿠팡':
        await coupang(message)

    elif message.channel.name == '금융':
        await finance(message)

    elif message.channel.name == '날씨':
        await weather(message)

    elif message.channel.name == '코로나-확진자':
        await covid19(message)

    elif message.channel.name == '이베스트공지':
        await ebest(message)


async def coupang(message):
    # http로 시작하고 coupang 포함 시 전달.

    if message.content.startswith('https://link.coupang.com/re/CSHARESDP?'):
        parts = urlparse(message.content)
        qs = dict(parse_qsl(parts.query))  # parse_qsl 결과를 dict로 캐스팅.

        # 본인 계정 lptag=###########  친구 계정 lptag=###########

        if qs['lptag'] == '###########':    # 본인 계정
            qs['lptag'] = '###########'     # 친구 계정
            # 본인 계정으로 쿠팡 결제 시 친구 계정에 리워드 쌓기

        elif qs['lptag'] == '###########':  # 친구 계정
              qs['lptag'] = '###########'   # 본인 계정
            # 친구 계정으로 쿠팡 결제 시 내 계정에 리워드 쌓기

        parts = parts._replace(query=urlencode(qs))  # dict인 qs를 urlencode에 넘겨 str 만들고 replace
        new_url = urlunparse(parts)
        print(new_url)

        if qs['lptag'] != '###########' and qs['lptag'] != '###########':
            new_url = '링크를 다시 확인하세요 !'  # REVIEW: new_url은 변수 이름이 url인데 메시지가 들어가므로 개선필요
            # 본인 혹은 친구의 lptag가 아닌 경우 링크 확인 메시지 띄우기
        await message.channel.send(new_url)


async def finance(message):
    # 국내금 국제금 달러 엔 / 크롤링 / 엔화 시세와 추이
    if message.content.startswith('달러'):

        html = urlopen('https://finance.yahoo.com/quote/usdkrw=x/?guccounter=1')
        bs = BeautifulSoup(html, 'html.parser')

        usd = bs.find('span', {'data-reactid': '32'}).text

        await message.channel.send(f':dollar: 실시간 1달러는 {usd}원! :dollar:')

    if message.content.startswith('엔'):

        html = urlopen('https://finance.naver.com/marketindex/exchangeDetail.nhn?marketindexCd=FX_JPYKRW')
        bs = BeautifulSoup(html, 'html.parser')

        td = bs.find('p', {'class': 'no_today'}).text
        jpy = td.replace('\n', '')

        await message.channel.send(f':yen: 오늘의 엔화는 100엔당 {jpy}!:yen: ' )

    if message.content.startswith('금'):
        """ 페이지소스 > Network > ListByDate > Response 확인 > Preview에서 깔끔하게 확인 > 실시간 데이터인지 확인 
        > Headers > Request Payload 확인 // 동적웹크롤"""

        html = urlopen('https://finance.naver.com/marketindex/goldDetail.nhn')
        bs = BeautifulSoup(html, 'html.parser')
        td = bs.find('p', {'class': 'no_today'}).text
        gold = td.replace('\n', '')

        await message.channel.send(f':coin: 오늘의 국내 금값: {gold}! :coin:')


async def weather(message):
    # 자양동 날씨를 날씨 파일로 저장해서 전날이랑 비교
    if message.content.startswith('자양'):

        html = urlopen('https://weather.naver.com/today/09215820')
        bs = BeautifulSoup(html, 'html.parser')

        tem = bs.find('strong', {'class': 'current'}).text
        yday = bs.find('span', {'class': 'temperature'}).text  # 온도는 높, 낮, 같을수 있음!
        icon = bs.find('span', {'class': 'weather before_slash'})

        pprint(icon)

        if '안개' in icon:
            icon = ':fog:'
        elif '맑음' in icon:
            icon = ':sunny:'
        elif '구름많음' in icon:
            icon = ':white_sun_cloud:'
        elif '구름조금' in icon:
            icon = ':white_sun_small_cloud:'
        elif '비' in icon:
            ':cloud_rain:'
        elif '흐림' in icon:
            icon = ':cloud:'
        elif '눈' in icon:
            icon = ':cloud_snow:'
        elif '번개' or '뇌우' in icon:
            icon = ':cloud_lightning:'

        await message.channel.send(f'{icon} 자양1동은 {tem}로 어제보다 {yday}')


async def covid19(message):
    if message.content.startswith('신규'):
        html = urlopen('https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=%EC%BD%94%EB%A1%9C%EB%82%98+%ED%99%95%EC%A7%84%EC%9E%90')
        bs = BeautifulSoup(html, 'html.parser')

        div = bs.find('div', {'class': 'status_today'}).text
        cases = div.replace('  ', '').strip(' ').split(' ')
        total = int(cases[2]) + int(cases[4])

        await message.channel.send(f':mask::loudspeaker: COVID-19 일일확진자: 국내발생 {cases[2]}명, 해외유입 {cases[4]}명. 총 {total}명')


async def ebest(message):
    if message.content.startswith('!'):
        await ebest_notice(message.channel, True)


async def ebest_notice(channel, notify_no_new):
    url = 'https://m.ebestsec.co.kr/etw/boardList'

    res = requests.post(url, data='page=1&perPage=15&board_no=77&category_no=&skey=&sval=', headers={
        'Referer': 'https://m.ebestsec.co.kr/',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
    })

    if res.status_code == requests.codes.ok:
        print('접속')
        post_data = json.loads(res.text)  # json object -> python dict

        # response 에서 데이터리스트 가져오고 리스트 저장, for 로 리스트읽음
        data_list = post_data['response']
        board_seq_list = []
        for data in data_list:  # type(data_list) = list
            board_seq_list.append(data['BOARD_SEQ'])

        # before file !
        with open('bef_Seq.json', 'r') as st_json:
            bef_seq = json.load(st_json)
            print('bef_seq: ')
            print(bef_seq)

        with open('bef_Seq.json', 'w') as json_file:
            json.dump(board_seq_list, json_file, indent=4)

        print('board_seq_list: ')
        print(board_seq_list)  # n p t

        if bef_seq == board_seq_list:
            ebest_msg = '새 공지 없음'

            if not notify_no_new:
                return

        elif bef_seq != board_seq_list:
            new_post_num = set(board_seq_list) - set(bef_seq)  # 차집합으로 효율적 알고리즘
            # new_post_num = [x for x in board_seq_list if x not in bef_seq]  # 비교연산이 많이 일어나서 비효율적. m*n만큼 일어남!
            pprint('new_post_num: ')
            pprint(new_post_num)
            ebest_msg = f'새 글 번호: {new_post_num}'

    else:
        client_errors = [400, 401, 403, 404, 408]
        server_errors = [500, 502, 503, 504]

        if res.status_code in client_errors:
            print(f'{res.status_code} : 클라이언트 에러')
            sys.exit(1)  # 비정상 종료 (에러)
        elif res.status_code in server_errors:
            print(f'{res.status_code} : 서버 에러')
            sys.exit(1)

    await channel.send(ebest_msg)

# TODO: DISCORD_TOKEN이 없을 경우 친절한 에러메시지 띄워주기

parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['ebest_notice', 'chatbot'], required=True)
args = parser.parse_args()

if args.mode == 'chatbot':
    client.run(os.environ['DISCORD_TOKEN'])

elif args.mode == 'ebest_notice':
    async def ebest_mode():
        try:
            await client.login(os.environ['DISCORD_TOKEN'])
            # print([guild async for guild in client.fetch_guilds()])
            guild = await client.fetch_guild(788754798493040650)
            channels = await guild.fetch_channels()
            channel = {
                channel.name: channel
                for channel in channels
            }['이베스트공지']
            await ebest_notice(channel, False)

        finally:
            await client.logout()

    asyncio.run(ebest_mode())
