# This Python file uses the following encoding: utf-8
# -*- coding: utf-8 -*-
# kunho.yoo
#%%
import requests
from urllib.parse import urlparse
import re
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from bs4 import BeautifulSoup

# 본문의 링크는 상대 경로이므로, 메인 url 정보에서 추출된 호스트 정보를 이용하여 절대 url 경로를 만
def make_doc_url(main_parts, url):
    if (not url):
        return None

    sub_parts = urlparse(url)
    sub_parts = sub_parts._replace(scheme = main_parts.scheme, netloc = main_parts.netloc)
    doc_url = sub_parts.geturl()
    return doc_url

# 주어진 링크의 본문을 크롤링하여 마침표 단위로 문장을 잘라 리스트로 변환
def get_doc_text_list(url):
    doc_req = requests.get(url)
    doc_soup = BeautifulSoup(doc_req.content, 'html.parser')

    # txt 또는 t_txt 태그 추출
    doc_text = doc_soup.select('p.txt') # or p.t_txt
    if (not doc_text):
        doc_text = doc_soup.select('p.t_txt') # or p.t_txt

    doc_text_list = []
    for text in doc_text:
        # 한글/숫자/공백/./,/?/!를 제외한 문자 제거
        # new_text = re.sub(r'[^ㄱ-ㅎ|ㅏ-ㅣ|가-힣|\d|\s|.|,|?|!]', '', text.text)
        new_text = re.sub(r'[^ㄱ-ㅎ|ㅏ-ㅣ|가-힣|\d| |.|,|?|!|~|#|$]', '', text.text)

        # 마침표 기준으로 문장 분리, 단 소수점이 있는 숫자는 제외
        doc_text_list.extend(re.split(r'(?<=[^0-9])\.', new_text))
    return doc_text_list

# 메인 페이지에서 기사 목록 갯수를 추출하여 전체 페이지 수 계산
def calculate_page_count(url):
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    # 전체 페이지 수 계산, 전체 건수 / 페이지당 링크 수(15)
    return round(int(re.sub(r'[^\d]', '', soup.select_one('div.path_area > em.count').text)) / 15 + 0.5)

# 주어진 링크를 시작으로 모든 기사를 크롤링
def start_web_crawling(url, save_path):
    main_parts = urlparse(url)              # 주어진 url 파싱
    total_page = calculate_page_count(url)  # 전체 페이지 수
    progressbar['maximum'] = total_page     # 진행바 크기 조정
    file_counter = 1                        # 파일 카운터
    line_counter = 0                        # 라인 카운터, 최대 10000

    # 001.txt부터 파일 생성
    fp = open(f'{save_path}/{file_counter:03d}.txt', 'w', encoding = 'utf-8')

    for page in range(1, total_page + 1):
        page_url = f'{url}&page={page}'     # 각 페이지 url 생성

        req = requests.get(page_url)        # 해당 페이 정보 가져오기
        page_soup = BeautifulSoup(req.content, 'html.parser')

        # 해당 페이지의 기사 목록 링크 추출
        links = page_soup.select('div.subject > strong.title > a')
        for link in links[::2]: # '담기' 링크 제외
            doc_url = make_doc_url(main_parts, link['href'].strip())
            doc_text_list = get_doc_text_list(doc_url)

            # 추출된 본문 내용을 줄 단위로 저장
            for text in doc_text_list:
                text = text.strip()
                #
                # 추가 검토 사항: 문장으로 볼 수 없는 짧은 길이의 결과는 처리할 필요가 있을까?
                #
                if (text):
                    # line_counter가 10000을 넘으면 새로운 파일을 만듬
                    if (line_counter >= 10000):
                        line_counter = 0
                        file_counter += 1
                        if (not fp.closed):
                            fp.close()
                        fp = open(f'{save_path}/{file_counter:03d}.txt', 'w', encoding = 'utf-8')

                    # 결과 저장
                    fp.write(f'{text}.\n')
                    line_counter += 1
            
            # 윈도우 갱신
            window.update()

            # 중단 버튼이 눌리면 열린 파일을 닫고 종료
            if (not start_flag):
                if (not fp.closed):
                    fp.close()
                return

        # 진행바 상태 업데이트
        progress_var.set(page)
        style.configure('text.Horizontal.TProgressbar', text = '{:g}/{} page'.format(progress_var.get(), total_page))
        window.update()

    # 열려있는 파일을 닫음
    if (not fp.closed):
        fp.close()

# 텍스트 추출 경로 설정
def open_save_path():
    global save_path
    save_path = filedialog.askdirectory()

# 웹 크롤링 시작
def click_start_crawling():
    global start_flag

    # 백과 소주제 링크 입력이 없으면 종료
    if (not link_url.get()):
        return

    # 추출 시작중이면 중단
    if (start_flag):
        start_flag = False
        return
    
    # 추출 시작하면 버튼의 상태 변경
    start_flag = True
    path_button['state'] = 'disabled'
    crawling_button['text'] = ' Txt 추출 중단 '

    start_web_crawling(link_url.get(), save_path)

    # 추출 완료 또는 중단되면 버튼 원 위치
    path_button['state'] = 'normal'
    crawling_button['text'] = ' Txt 추출 시작 '


window = tk.Tk()
window.title('네이버 백과 카테고리 텍스트 크롤링')

start_flag = False              # 추출 시작/중단 플래그
save_path = './'                # 저장 경로
link_url = tk.StringVar()       # 백과 소주제 링크
link_url.set('https://terms.naver.com/list.naver?cid=50998&categoryId=50998')
progress_var = tk.DoubleVar()   # 진행바 변수

ttk.Label(window, text = '백과 소주제 링크 입력:', relief = 'groove', anchor = 'center').grid(row = 0, column = 0, columnspan = 2, sticky = 'we', padx = 5, pady = 5)
ttk.Entry(window, textvariable = link_url, width = 80).grid(row = 0, column = 2, sticky = 'we', padx = 5, pady = 5)

path_button = ttk.Button(window, text = ' Txt 추출 경로 설정 ', command = open_save_path, width = 20)
path_button.grid(row = 1, column = 0, sticky = 'we', padx = 5, pady = 5)

crawling_button = ttk.Button(window, text = ' Txt 추출 시작 ', command = click_start_crawling, width = 20)
crawling_button.grid(row = 1, column = 1, sticky = 'we', padx = 5, pady = 5)

# 진행바 스타일 정의
style = ttk.Style(window)
style.layout('text.Horizontal.TProgressbar', 
             [('Horizontal.Progressbar.trough',
               {'children': [('Horizontal.Progressbar.pbar',
                              {'side': 'left', 'sticky': 'ns'})],
                'sticky': 'nswe'}), 
              ('Horizontal.Progressbar.label', {'sticky': ''})])
style.configure('text.Horizontal.TProgressbar', text = '0/0 page')

progressbar = ttk.Progressbar(window, maximum = 100, variable = progress_var, style = 'text.Horizontal.TProgressbar')
progressbar.grid(row = 1, column = 2, sticky = 'we', padx = 5, pady = 5)

window.mainloop()
