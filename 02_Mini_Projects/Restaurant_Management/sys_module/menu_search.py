import json
from db_connect import db  # DB 커넥션 모듈
from flask import render_template

# 메뉴 검색
def getSearchMenu(searchmenu, user):
    storename = storeName(user)
    conn = db.getConnection()
    cur = conn.cursor()
    result = 0
    args = (searchmenu, result, storename)
    cur.callproc("store_menu_search", args)  # out파라미터 없이 메뉴 검색 프로시저

    # SELECT 결과 받기
    menu_data = cur.fetchone() # select문을 써놓으면 fetch구문으로 꺼내서 쓸 수 있다고 함.(pymysql을 쓰고 있으면)

    # 검색 result 값 받기(검색 데이터 있으면 1, 없으면 2, 에러 -1)
    cur.execute("SELECT @_store_menu_search_1;")  # OUT 파라미터 위치는 두 번째
    result_code = cur.fetchone()[0]

    cur.close()
    conn.close()
    
    # 결과 데이터 json으로 변환
    response = json.dumps({'result_code': result_code,  'menu_data': menu_data}, ensure_ascii=False)

    return response

# 사용자 기반 가게이름 조회
def storeName(user):
    conn = db.getConnection()
    cur = conn.cursor()
    cur.execute(""" 
                SELECT s.storename
                FROM user u
                join store s on u.storecode  = s.storecode
                WHERE userid = %s ;
                """, user)
    storename = cur.fetchone()[0]
    return storename
# 로그인 사용자 가게 코드 조회
def storeCode(user):
    conn = db.getConnection()
    cur = conn.cursor()
    cur.execute(""" SELECT u.storeCode 
                    FROM user u 
                    join store s on u.storecode = s.storecode
                    WHERE userid = %s ;
                """, user)
    storeCode = cur.fetchone()[0]
    return storeCode

# Top5 메뉴 검색
def hitMenu(storename):
    conn = db.getConnection()
    cur = conn.cursor()
    cur.callproc("menu_top_ranks", (storename,))  # out파라미터 없이 메뉴 검색 프로시저
    topMenuList = cur.fetchall()
    cur.close()
    conn.close()

    response = json.dumps([
        {
            "no": item[0],
            "storename": item[1],
            "menuname": item[2],
            "price": item[3],
            "amount": item[4],
            "total": item[5],
            "sales_rank": item[6]
        }
        for item in topMenuList
    ], ensure_ascii=False)

    return response